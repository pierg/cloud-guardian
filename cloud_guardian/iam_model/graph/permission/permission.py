import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List

from cloud_guardian.iam_model.graph.permission.actions import (
    ActionFactory,
    SupportedAction,
)
from cloud_guardian.iam_model.graph.permission.conditions import (
    ConditionFactory,
    SupportedCondition,
)
from cloud_guardian.iam_model.graph.permission.effects import Effect


@dataclass
class Permission:
    id: str
    action: SupportedAction
    effect: Effect
    conditions: List[SupportedCondition]

    def __str__(self):
        conditions_str = "\n".join(str(condition) for condition in self.conditions)
        return f"Action: {self.action}\nEffect: {self.effect}\nConditions: [{conditions_str}]\n"

    @classmethod
    def from_dict(cls, permission_dict: Dict[str, Any]) -> List["Permission"]:
        effect = Effect(permission_dict["Effect"])
        actions = [
            ActionFactory.get_or_create(action) for action in permission_dict["Action"]
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
        action: SupportedAction,
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
            actions = [ActionFactory.get_or_create(permission_dict["Action"])]
        else:
            actions = [
                ActionFactory.get_or_create(action)
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
        action: SupportedAction, effect: Effect, conditions: List[SupportedCondition]
    ) -> str:
        action_effect = f"{action.aws_action}{effect}"
        conditions_str = "".join(sorted(str(c) for c in conditions))
        return hashlib.sha256(f"{action_effect}{conditions_str}".encode()).hexdigest()


permission_data = {
    "Effect": "Allow",
    "Action": ["sts:AssumeRole", "s3:CopyObject"],
    "Principal": {
        "AWS": [
            "arn:aws:iam::123456789012:user/Alice",
            "arn:aws:iam::123456789012:user/Bob",
        ]
    },
    "Condition": {
        "DateGreaterThan": {"aws:CurrentTime": "2023-01-01T00:00:00Z"},
        "IpAddress": {"aws:SourceIp": "203.0.113.0/24"},
    },
    "Resource": "arn:aws:s3:::example-bucket/*",
}

permissions = PermissionFactory.from_dict(permission_data)
for perm in permissions:
    print(perm)
