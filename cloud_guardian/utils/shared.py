import json
from pathlib import Path

repo_path = Path(__file__).parent.parent.parent

data_path = repo_path / "data"

output_path = repo_path / "output"

constraints_path = data_path / "constraints.json"


def load_config(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


constraints_data = load_config(constraints_path)
constraints_actions = constraints_data["actions"]
constraints_conditions = constraints_data["conditions"]
