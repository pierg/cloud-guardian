import ipaddress
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Union

from cloud_guardian.iam_model.validating import Validate


class IAMAction(Enum):
    """Defines the actions that can be performed on an IAM resource."""

    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    FULL_CONTROL = auto()
    ASSUME_ROLE = auto()
    PART_OF = auto()

    @classmethod
    def from_string(cls, action_str: str) -> "IAMAction":
        """Create an IAMAction object from a string representation."""
        if action_str:
            for action in cls:
                if action.name.lower() == action_str.lower():
                    return action
        return None


class Effect(Enum):
    ALLOW = auto()
    DENY = auto()


@dataclass
class Condition:
    """Defines a condition under which a permission is granted."""

    condition_key: str
    condition_operator: str
    condition_value: Any

    @classmethod
    def from_string(cls, condition_str: str) -> "Condition":
        """Create a Condition object from a string representation."""
        if not condition_str:
            raise ValueError("Condition string must not be empty.")

        parts = condition_str.split("==")
        if len(parts) != 2:
            raise ValueError(f"Invalid condition format: {condition_str}")

        condition_key, condition_value = parts[0], cls.parse_condition_value(parts[1])
        return cls(condition_key, "equals", condition_value)

    @staticmethod
    def parse_condition_value(value_str: str) -> Any:
        """Parse the condition value from a string, detecting types and ranges."""
        if "-" in value_str:
            return value_str  # Assumed to be a range; further parsing depends on the condition type
        try:
            # Attempt to parse as integer
            return int(value_str)
        except ValueError:
            pass
        try:
            # Attempt to parse as IP address or network
            return (
                ipaddress.ip_address(value_str)
                if "/" not in value_str
                else ipaddress.ip_network(value_str)
            )
        except ValueError:
            pass
        # Default to string if no other types match
        return value_str

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against the provided context."""
        context_value = context.get(self.condition_key)
        if self.condition_operator == "equals":
            return context_value == self.condition_value
        elif self.condition_operator == "not_equals":
            return context_value != self.condition_value
        elif self.condition_operator == "in_range":
            if isinstance(self.condition_value, str) and "-" in self.condition_value:
                # Handling range for integers as an example
                start, end = map(int, self.condition_value.split("-"))
                return start <= context_value <= end
            elif isinstance(self.condition_value, ipaddress.IPv4Network) or isinstance(
                self.condition_value, ipaddress.IPv6Network
            ):
                return ipaddress.ip_address(context_value) in self.condition_value
        elif self.condition_operator == "time_between":
            # Assuming context_value is a string in "%H:%M" format
            context_time = datetime.strptime(context_value, "%H:%M").time()
            start_time, end_time = [
                datetime.strptime(t, "%H:%M").time()
                for t in self.condition_value.split("-")
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
    conditions: List[Condition] = field(default_factory=list)

    @classmethod
    def from_string(cls, action_with_effect: str, condition: str) -> "Permission":
        if not condition:
            conditions = []
        else:
            conditions = [Condition.from_string(condition)]
        if action_with_effect.startswith("~"):
            effect = Effect.DENY
            action = IAMAction.from_string(action_with_effect[1:])
        else:
            effect = Effect.ALLOW
            action = IAMAction.from_string(action_with_effect)

        print(
            f"Creating permission {action_with_effect} with effect {effect} for action {action} and conditions {conditions}"
        )
        return cls(action_with_effect, effect, action, conditions)

    def add_condition(self, condition: Condition):
        """Add a condition to the permission."""
        self.conditions.append(condition)

    def is_granted(self, context: Dict[str, Any]) -> bool:
        """Determine if the permission is granted based on the conditions."""
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        return self.effect == Effect.ALLOW

    @property
    def label(self) -> str:
        """Generates a numerical label for the permission, including a tilde for negative effects."""
        numeric_label = self.action.value
        if self.effect == Effect.DENY:
            return f"~{numeric_label}"
        return str(numeric_label)

    def is_flow_active(self, context: Union[Dict[str, Any] | None]) -> bool:
        """Determine if the flow is active based on the type of action and conditions."""
        if context:
            for condition in self.conditions:
                if not condition.evaluate(context):
                    return False
        return Validate.is_action_flow_enabler(self.action)
