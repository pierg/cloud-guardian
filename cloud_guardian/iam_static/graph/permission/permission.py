import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from cloud_guardian.iam_static.graph.permission.actions import (
    ActionsFactory,
    SpecifiedActions,
)
from cloud_guardian.iam_static.graph.permission.conditions import (
    ConditionFactory,
    SupportedCondition,
)
from cloud_guardian.iam_static.graph.permission.effects import Effect


# the rank of a permission identifies it applies by definition
# to a single entity (monadic) or to pair of entities (dyadic)
class PermissionRank(Enum):
    MONADIC = 1
    DYADIC = 2


@dataclass
class Permission:
    id: str

    action: SpecifiedActions
    effect: Effect
    conditions: List[SupportedCondition]

    # either
    # - monadic (attached to a node) or
    # - dyadic (attached to a pair of nodes)
    rank: Optional[PermissionRank] = None

    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return (
            self.id,
            self.action.aws_action_pattern,
            self.effect.name,
            tuple(self.conditions),
            self.rank,
        ) == (
            other.id,
            other.action.aws_action_pattern,
            other.effect.name,
            tuple(other.conditions),
            other.rank,
        )

    def __hash__(self):
        return hash(
            (
                self.id,
                self.action.aws_action_pattern,
                self.effect.name,
                tuple(self.conditions),
                self.rank,
            )
        )

    def __str__(self):
        conditions_str = "\n".join(str(condition) for condition in self.conditions)
        return f"Action: {self.action}\nEffect: {self.effect}\nConditions: [{conditions_str}]\n"

    def __post_init__(self):
        # set the permission rank
        custom_ranks = {
            "create": PermissionRank.MONADIC,
            # add more keywords and their corresponding ranks here
        }

        # rank already set? skip
        if self.rank is not None:
            return

        for keyword, custom_rank in custom_ranks.items():
            if keyword in self.action.id.lower():
                self.rank = custom_rank
                break
        else:
            # rank is dyadic by default
            self.rank = PermissionRank.DYADIC

    @classmethod
    def from_dict(cls, permission_dict: Dict[str, Any]) -> List["Permission"]:
        effect = Effect(permission_dict["Effect"])
        actions = [
            ActionsFactory.get_or_create(action) for action in permission_dict["Action"]
        ]
        conditions = []
        if "Condition" in permission_dict:
            for condition_type, details in permission_dict["Condition"].items():
                condition = ConditionFactory.get_or_create({condition_type: details})
                conditions.append(condition)

        return [
            cls(action=action, effect=effect, conditions=conditions)
            for action in actions
        ]

    def is_granted(self, runtime_values: Dict[str, Any]) -> bool:
        for condition in self.conditions:
            if not condition.evaluate(runtime_values.get(condition.condition_key)):
                return False
        return self.effect == Effect.ALLOW


class PermissionFactory:
    _instances = {}

    @classmethod
    def get_or_create(
        cls,
        action: SpecifiedActions,
        effect: Effect,
        conditions: List[SupportedCondition],
        rank: Optional[PermissionRank] = None,
    ) -> Permission:
        permission_id = cls._create_id(action, effect, conditions)

        if permission_id not in cls._instances:
            # Create the Permission with the generated ID
            cls._instances[permission_id] = Permission(
                id=permission_id,
                action=action,
                effect=effect,
                conditions=conditions,
                rank=rank,
            )
        return cls._instances[permission_id]

    @classmethod
    def from_dict(cls, permission_dict: Dict[str, Any]) -> List[Permission]:
        effect = Effect(permission_dict["Effect"])
        if isinstance(permission_dict["Action"], str):
            actions = [ActionsFactory.get_or_create(permission_dict["Action"])]
        else:
            actions = [
                ActionsFactory.get_or_create(action)
                for action in permission_dict["Action"]
            ]
        conditions = []
        if "Condition" in permission_dict:
            for condition_type, details in permission_dict["Condition"].items():
                condition = ConditionFactory.from_dict({condition_type: details})
                conditions.append(condition)

        return [cls.get_or_create(action, effect, conditions) for action in actions]

    @staticmethod
    def from_policy_document(policy_document: Dict[str, Any]) -> List[Permission]:
        permissions = []
        for statement in policy_document["Statement"]:
            permissions.extend(PermissionFactory.from_dict(statement))
        return permissions

    @staticmethod
    def _create_id(
        action: SpecifiedActions, effect: Effect, conditions: List[SupportedCondition]
    ) -> str:
        action_effect = f"{action.aws_action_pattern}{effect}"
        conditions_str = "".join(sorted(str(c) for c in conditions))
        return hashlib.sha256(f"{action_effect}{conditions_str}".encode()).hexdigest()
