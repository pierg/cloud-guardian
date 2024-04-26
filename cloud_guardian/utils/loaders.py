import json
import os
import re
from pathlib import Path

from arnparse import arnparse
from cloud_guardian import logger


def load_iam_data_into_dictionaries(data_folder: Path):
    # Initialize dictionaries for each JSON file
    groups_data = {}
    policies_data = {}
    roles_data = {}
    users_data = {}

    # Mapping of file names to dictionaries
    file_to_dict = {
        "groups.json": groups_data,
        "policies.json": policies_data,
        "roles.json": roles_data,
        "users.json": users_data,
    }

    # Read each file and load its content into the corresponding dictionary
    for file_name, data_dict in file_to_dict.items():
        file_path = os.path.join(data_folder, file_name)
        try:
            with open(file_path, "r") as file:
                data_dict.update(json.load(file))
        except FileNotFoundError:
            print(f"Warning: {file_name} not found in {data_folder}")
        except json.JSONDecodeError:
            print(f"Error: {file_name} could not be decoded as JSON.")

    # Return the dictionaries
    return groups_data, policies_data, roles_data, users_data


def extract_bucket_names(policy):
    bucket_names = set()
    statements = policy["PolicyDocument"]["Statement"]
    for statement in statements:
        resources = statement["Resource"]
        for resource in resources:
            try:
                parsed_arn = arnparse(resource)
                bucket_name = re.sub(r"[^a-zA-Z]+$", "", parsed_arn.resource)
                bucket_names.add(bucket_name)
            except Exception:
                logger.error(f"Cannot parse bucket ARN: {resource}")
    return list(bucket_names)
