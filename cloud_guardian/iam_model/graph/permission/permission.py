import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List

from cloud_guardian.iam_model.graph.permission.actions import (
    ActionsFactory,
    SpecifiedActions,
)
from cloud_guardian.iam_model.graph.permission.conditions import (
    ConditionFactory,
    SupportedCondition,
)
from cloud_guardian.iam_model.graph.permission.effects import Effect


@dataclass
class Permission:
    id: str
    action: SpecifiedActions
    effect: Effect
    conditions: List[SupportedCondition]

    def __str__(self):
        conditions_str = "\n".join(str(condition) for condition in self.conditions)
        return f"Action: {self.action}\nEffect: {self.effect}\nConditions: [{conditions_str}]\n"

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
    ) -> Permission:
        permission_id = cls._create_id(action, effect, conditions)

        if permission_id not in cls._instances:
            # Create the Permission with the generated ID
            cls._instances[permission_id] = Permission(
                id=permission_id, action=action, effect=effect, conditions=conditions
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
    def _create_id(
        action: SpecifiedActions, effect: Effect, conditions: List[SupportedCondition]
    ) -> str:
        action_effect = f"{action.aws_action_pattern}{effect}"
        conditions_str = "".join(sorted(str(c) for c in conditions))
        return hashlib.sha256(f"{action_effect}{conditions_str}".encode()).hexdigest()
