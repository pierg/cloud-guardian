
from cloud_guardian import logger
from cloud_guardian.utils.strings import strip_s3_resource_id


class BiMap:
    def __init__(self):
        self.map = {}
        self.reverse_map = {}

    def add(self, key, value):
        if not (
            isinstance(key, (int, str, float, tuple))
            and isinstance(value, (int, str, float, tuple))
        ):
            raise ValueError(
                "Keys and values must be hashable types (int, str, float, tuple)"
            )
        if key in self.map:
            if self.map[key] != value:
                raise ValueError(
                    f"Cannot add key {key} with a {value}; existing value is different ({self.map[key]})."
                )
            else:
                logger.info(
                    f"Ignoring addition of existing key-value pair {key} -> {value}"
                )
        else:
            logger.info(f"Adding {key} -> {value}")
            self.map[key] = value
            self.reverse_map[value] = key

    def remove(self, key):
        if not isinstance(key, (int, str, float, tuple)):
            raise ValueError("Key must be a hashable type")
        if key in self.map:
            value = self.map.pop(key)
            self.reverse_map.pop(value, None)
        else:
            raise KeyError(f"Key '{key}' not found and cannot be removed.")

    def get(self, key):
        if not isinstance(key, (int, str, float, tuple)):
            raise ValueError(
                f"Key must be a hashable type. Received {type(key).__name__} which is not."
            )
        return self.map.get(key) or self.reverse_map.get(key)

    def contains(self, key):
        return key in self.map or key in self.reverse_map

    def print_table(self):
        print(f"{'Key'.ljust(30)} | {'Value'.ljust(30)}")
        print("-" * 63)
        for key, value in self.map.items():
            print(f"{key.ljust(30)} | {value.ljust(30)}")


def get_all_principals_ids(policy_dict: dict) -> list[str]:
    return [
        statement["Principal"]["ID"]
        for statement in policy_dict["PolicyDocument"]["Statement"]
    ]


def get_all_resources_ids(policy_dict: dict) -> list[str]:
    return [
        resource
        for statement in policy_dict["PolicyDocument"]["Statement"]
        for resource in statement["Resource"]
    ]


def substitute_values(data: dict, mapping: BiMap) -> dict:
    """
    Recursively substitute values in a dictionary using provided mapping.
    If they exist in the mapping, modify them by appending necessary suffixes.
    """

    def recurse(item):
        if isinstance(item, dict):
            # Handle dictionary recursively
            return {k: recurse(v) for k, v in item.items()}
        elif isinstance(item, list):
            # Process each element in the list, specially handle 'Resource' arrays
            return [recurse(x) for x in item]
        elif isinstance(item, str):
            # Process string values, checking for specific Resource replacements
            base_id = strip_s3_resource_id(item)
            if mapping.contains(base_id):
                # Replace base id and append any suffix from the original string
                # Capture the remaining suffix after the base id
                suffix = item[len(base_id) :]
                return mapping.get(base_id) + suffix
            else:
                return item
        else:
            # Return other types unchanged
            return item

    return recurse(data)
