from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from cloud_guardian.iam_model.graph.edges.action import IAMAction
from cloud_guardian.iam_model.graph.edges.condition import Condition
from cloud_guardian.iam_model.graph.edges.effect import Effect


@dataclass
class Permission:
    effect: Effect
    action: IAMAction
    conditions: List[Condition] = field(default_factory=list)

    @classmethod
    def from_string(
        cls, action_with_effect: str, conditions_str: List[str]
    ) -> "Permission":
        effect = Effect.from_string(action_with_effect)
        action_str = action_with_effect.lstrip("~")
        action = IAMAction.from_string(action_str)
        conditions = [
            Condition.from_string(condition_str) for condition_str in conditions_str
        ]

        return cls(effect=effect, action=action, conditions=conditions)

    def add_condition(self, condition: Condition):
        self.conditions.append(condition)

    def is_granted(self, context: Dict[str, Any]) -> bool:
        return (
            all(condition.evaluate(context) for condition in self.conditions)
            and self.effect == Effect.ALLOW
        )

    @property
    def id(self) -> str:
        """Generates a unique ID for the permission, including a tilde for negative effects."""
        return f"{self.effect.to_symbol()}{self.action.name}"

    @property
    def label(self) -> str:
        """Generates a label for the permission, including a tilde for negative effects."""
        return f"{self.effect.to_symbol()}{self.action.name}"

    def is_flow_active(self, context: Union[Dict[str, Any], None] = None) -> bool:
        """Determine if the flow is active based on the type of action and conditions."""

        conditions_check = all(
            condition.evaluate(context) for condition in self.conditions
        )
        action_check = self.action.flow_enabler
        effect_check = self.effect == Effect.ALLOW
        return conditions_check and action_check and effect_check

    def is_action_denied(self) -> bool:
        """Check if the permission is set to deny."""
        return self.effect == Effect.DENY
