import json
from pathlib import Path


def load_iam_json_data(data_folder: Path):
    json_files = [
        "groups.json",
        "identities_policies.json",
        "resources_policies.json",
        "roles.json",
        "users.json",
    ]
    data = {}
    for file_name in json_files:
        file_path = data_folder / file_name
        if file_path.exists():
            with open(file_path, "r") as file:
                data[file_name] = json.load(file)
        else:
            data[file_name] = {}
    return data
