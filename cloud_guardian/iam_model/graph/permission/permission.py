from dataclasses import dataclass, field
from typing import List, Dict, Any
from actions import SupportedAction, ActionFactory
from conditions import SupportedCondition, ConditionFactory
from effects import Effect
import hashlib


@dataclass
class Permission:
    action: SupportedAction
    effect: Effect
    conditions: List[SupportedCondition]
    
    id: str = field(init=False)

    def __post_init__(self):
        condition_str = ''.join(str(c) for c in self.conditions)
        combined = f"{self.action.aws_action}{self.effect}{condition_str}"
        self.id = hashlib.sha256(combined.encode()).hexdigest()

    def __str__(self):
        conditions_str = '\n'.join(str(condition) for condition in self.conditions)
        return f"Action:\t\t{self.action}\nEffect:\t\t{self.effect}\nConditions:\t\t [{conditions_str}\n"        

    @classmethod
    def from_dict(cls, permission_dict: Dict[str, Any]) -> List["Permission"]:
        effect = Effect(permission_dict["Effect"])
        actions = [ActionFactory.get_action(action) for action in permission_dict["Action"]]
        conditions = []
        if "Condition" in permission_dict:
            for condition_type, details in permission_dict["Condition"].items():
                condition = ConditionFactory.create_condition({condition_type: details})
                conditions.append(condition)

        return [cls(action=action, effect=effect, conditions=conditions) for action in actions]

    def is_granted(self, runtime_values: Dict[str, Any]) -> bool:
        for condition in self.conditions:
            if not condition.evaluate(runtime_values.get(condition.condition_key)):
                return False
        return self.effect == Effect.ALLOW



permission_data = {
    "Effect": "Allow",
    "Action": ["sts:AssumeRole", "s3:CopyObject"],
    "Principal": {
              "AWS": [
                "arn:aws:iam::123456789012:user/Alice",
                "arn:aws:iam::123456789012:user/Bob"
              ]
            },
    "Condition": {
        "DateGreaterThan": {
            "aws:CurrentTime": "2023-01-01T00:00:00Z"
        },
        "IpAddress": {
            "aws:SourceIp": "203.0.113.0/24"
        }
    },
    "Resource": "arn:aws:s3:::example-bucket/*",
}

permissions = Permission.from_dict(permission_data)
for perm in permissions:
    print(perm)
