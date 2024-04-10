from enum import Enum

from cloud_guardian.utils.shared import constraints_actions


class BaseIAMAction(Enum):
    @property
    def flow_enabler(self) -> bool:
        return self.value.get("flow_enabler", False)

    @property
    def description(self) -> str:
        return self.value.get("description", "")

    @property
    def allowed_between(self) -> list[tuple[list[str], list[str]]]:
        """Returns a list of allowed source-target pairs for the action."""
        allowed_between_data = self.value.get("allowed_between", [])
        allowed_between = [
            (relation["source"], relation["target"])
            for relation in allowed_between_data
        ]
        return allowed_between


def create_iam_action_enum(actions_data):
    enum_members = {
        action.upper(): properties for action, properties in actions_data.items()
    }
    IAMAction = Enum("IAMAction", enum_members, type=BaseIAMAction)
    return IAMAction


IAMAction = create_iam_action_enum(constraints_actions)
