import ipaddress
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Union
from xml.dom.minidom import Entity

from iam_model.entities import Resource


class IAMAction(Enum):
    """Defines the actions that can be performed on an IAM resource.
    Keeps track of the action that are 'flowEnabler' actions."""

    READ = (auto(), False)
    WRITE = (auto(), False)
    EXECUTE = (auto(), False)
    FULL_CONTROL = (auto(), False)
    ASSUME_ROLE = (auto(), True)  # Marked as flowEnabler
    PART_OF = (auto(), True)  # Marked as flowEnabler

    def __init__(self, _, flowEnabler):
        self.flowEnabler = flowEnabler


class Effect(Enum):
    ALLOW = auto()
    DENY = auto()


@dataclass
class Condition:
    """Defines a condition under which a permission is granted."""

    condition_key: str
    condition_operator: str
    condition_value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against the provided context."""
        context_value = context.get(self.condition_key)

        if self.condition_operator == "equals":
            return context_value == self.condition_value
        elif self.condition_operator == "not_equals":
            return context_value != self.condition_value
        elif self.condition_operator == "in_range":
            # Assuming IP range for simplicity; adjust as needed
            return ipaddress.ip_address(context_value) in ipaddress.ip_network(
                self.condition_value
            )
        elif self.condition_operator == "time_between":
            # Convert context_value to datetime for comparison
            time_format = "%H:%M"
            context_time = datetime.strptime(context_value, time_format).time()
            start_time, end_time = [
                datetime.strptime(t, time_format).time() for t in self.condition_value
            ]
            return start_time <= context_time <= end_time
        else:
            raise ValueError(
                f"Unsupported condition operator: {self.condition_operator}"
            )


@dataclass
class Permission:
    """Defines a permission with an effect, action, and target (Resource or Entity), and conditions."""

    id: str
    effect: Effect
    action: IAMAction
    target: Union[Resource, Entity]
    conditions: List[Condition] = field(default_factory=list)

    def is_granted(self, context: Dict[str, Any]) -> bool:
        """Determine if the permission is granted based on the conditions."""
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        return self.effect == Effect.ALLOW
