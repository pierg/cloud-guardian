
from cloud_guardian import logger
from cloud_guardian.utils.strings import strip_s3_resource_id


class BiMap:
    def __init__(self):
        self.arn_to_ids = {}
        self.ids_to_arn = {}

    def add(self, arn: str, id: str):
        if not (
            isinstance(arn, (str))
            and isinstance(id, (str))
        ):
            raise ValueError(
                "Keys and values must be hashable types (str)"
            )
        if arn in self.arn_to_ids:
            if self.arn_to_ids[arn] != id:
                raise ValueError(
                    f"Cannot add key {arn} with a {id}; existing value is different ({self.arn_to_ids[arn]})."
                )
            else:
                logger.info(
                    f"Ignoring addition of existing key-value pair {arn} -> {id}"
                )
        else:
            logger.info(f"Adding {arn} -> {id}")
            self.arn_to_ids[arn] = id
            self.ids_to_arn[id] = arn

    def remove_arn(self, arn):
        if not isinstance(arn, (str)):
            raise ValueError("Key must be a hashable type")
        if arn in self.arn_to_ids:
            value = self.arn_to_ids.pop(arn)
            self.ids_to_arn.pop(value, None)
        else:
            raise KeyError(f"Key '{arn}' not found and cannot be removed.")

    def get_arn(self, id):
        if not isinstance(id, (str)):
            raise ValueError(
                f"Key must be a hashable type. Received {type(id).__name__} which is not."
            )
        base_id = strip_s3_resource_id(id)        
        arn = self.ids_to_arn.get(base_id)
        if arn is None:
            logger.warning(f"Key {id} not found in mapping.")
            return None
        logger.info(f"Getting ARN for {id}: {arn}")
        suffix = id[len(base_id) :]
        return arn + suffix
        
    
    def get_id(self, arn):
        if not isinstance(arn, (str)):
            raise ValueError(
                f"Key must be a hashable type. Received {type(arn).__name__} which is not."
            )
        base_arn = strip_s3_resource_id(arn)        
        id = self.ids_to_arn.get(base_arn)
        if id is None:
            logger.warning(f"Key {arn} not found in mapping.")
            return None
        logger.info(f"Getting ID for {arn}: {id}")
        suffix = arn[len(base_arn) :]
        return id + suffix

    def print_table(self):
        print(f"{'Key'.ljust(30)} | {'Value'.ljust(30)}")
        print("-" * 63)
        for key, value in self.arn_to_ids.items():
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
                return mapping.get_arn(base_id) + suffix
            else:
                return item
        else:
            # Return other types unchanged
            return item

    return recurse(data)




def update_arns(data: dict, mapping: BiMap):
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if isinstance(value, (dict, list)):
                update_arns(value, mapping)
            else:
                new_value = mapping.get_arn(value)
                if new_value is not None:
                    data[key] = new_value
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, (dict, list)):
                update_arns(item, mapping)
            else:
                new_value = mapping.get_arn(item)
                if new_value is not None:
                    data[index] = new_value

