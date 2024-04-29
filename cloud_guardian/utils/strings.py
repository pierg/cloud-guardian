import json
import re
from datetime import datetime
from typing import Tuple


def get_name_and_type_from_id(id: str) -> Tuple[str, str]:
    """
    Extracts the name and type from a resource identifier.

    The function handles two main types of resource identifiers:
    1. Custom identifiers for S3 that start with "_custom_s3_id_:".
    2. Standard resource paths with types such as user, role, group, policy
    """

    # Handling S3 identifiers specifically
    if "s3" in id:
        # Strip the leading identifier type part and split by '/' to handle cases with paths
        return extract_resource_name(strip_s3_resource_id(id)), "s3"

    # Split the ID based on '/'
    id_parts = id.split("/")
    if len(id_parts) < 2:
        # If there is no "/" or insufficient parts to determine type and name
        raise ValueError("Invalid resource ID format.")

    # Extract the type and name from the last two parts of the split ID
    id_type, id_name = id_parts[-2], id_parts[-1]

    if "user" in id_type:
        return id_name, "user"
    elif "role" in id_type:
        return id_name, "role"
    elif "group" in id_type:
        return id_name, "group"
    elif "policy" in id_type:
        return id_name, "policy"
    else:
        # Handle unexpected types by raising an error
        raise ValueError(f"Unknown resource type: {id_type}")


def strip_s3_resource_id(id: str) -> str:
    # Regular expression to find the part until the first slash after the first colon
    match = re.match(r"([^:]+:[^/]*).*", id)
    if match:
        return match.group(1)
    return id


def extract_resource_name(s3_id: str) -> str:
    # Split the string by ":" and return the second part
    parts = s3_id.split(":")
    return parts[1] if len(parts) > 1 else ""


def datetime_serializer(o):
    """Custom serializer for datetime objects."""
    if isinstance(o, datetime):
        return o.isoformat()  # Convert datetime to ISO 8601 string format
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def pretty_print(obj):
    if isinstance(obj, dict):
        # Use the custom serializer for datetime objects
        print(json.dumps(obj, indent=4, default=datetime_serializer))
    else:
        print(obj)
