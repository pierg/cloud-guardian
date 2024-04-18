import json
from pathlib import Path

repo_path = Path(__file__).parent.parent.parent

data_path = repo_path / "data"

output_path = repo_path / "output"

identities_path = data_path / "identities.json"

actions_path = data_path / "actions.json"


def load_config(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def extract_conditions(data):
    allowed_between_values = {}
    for category, actions in data["actions"].items():
        for action, details in actions.items():
            if "allowed_between" in details:
                allowed_between_values[action] = details["allowed_between"]
    return allowed_between_values


actions = load_config(actions_path)
constraints_conditions = extract_conditions(actions)
