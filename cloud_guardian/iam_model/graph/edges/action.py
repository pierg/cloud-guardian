from enum import Enum

from cloud_guardian.utils.shared import constraints_actions
import json
from enum import Enum
from cloud_guardian.utils.shared import actions_path


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


def load_actions_from_json(json_file_path: str):
    with open(json_file_path, "r") as file:
        data = json.load(file)
        return data["actions"]


def create_iam_action_enum(actions_data):
    enum_members = {}
    for category, category_actions in actions_data.items():
        for action, properties in category_actions.items():
            enum_members[action.upper()] = properties
    IAMAction = Enum("IAMAction", enum_members, type=BaseIAMAction)
    return IAMAction


actions_data = load_actions_from_json(actions_path)
IAMAction = create_iam_action_enum(actions_data)
