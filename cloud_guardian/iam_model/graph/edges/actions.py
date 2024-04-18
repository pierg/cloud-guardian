import re
from dataclasses import dataclass, field
from typing import Dict, Type

from loguru import logger


@dataclass(frozen=True)
class IAMActionType:
    id: str  # e.g. "PolicyManagement"
    category: str  # e.g. "IAM"
    description: str
    regex_aws_action: str
    attributes: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        logger.info(f"ActionType instance created: {self.id}")

    @staticmethod
    def create_from_dict(
        class_name: str, class_attrs: Dict[str, any]
    ) -> Type["IAMActionType"]:
        logger.info(f"Creating action type {class_name}")
        return type(class_name, (IAMActionType,), class_attrs)

    def get_all_actions(self) -> list[str]:
        actions = re.findall(r"iam:\((.*?)\)", self.regex_aws_action)
        if actions:
            return actions[0].split("|")
        return []

    def is_action_allowed(self, action: str) -> bool:
        return action in self.get_all_actions()
