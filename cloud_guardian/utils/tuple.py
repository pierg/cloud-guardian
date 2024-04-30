import json
import uuid
from dataclasses import dataclass
from enum import Enum

import joblib
import pandas as pd
from cloud_guardian.utils.shared import data_path

class EntityType(Enum):
    SOURCE = "source"
    TARGET = "target"


class SourceType(Enum):
    USER = "user"
    GROUP = "group"
    ROLE = "role"


class TargetType(Enum):
    S3 = "s3"
    POSTGRESQL = "postgresql"


class Entity:
    def __init__(self, entity_type, entity_category, name, id):
        self.entity_type = entity_type
        self.entity_category = entity_category
        self.name = name
        self.id = id

    def __str__(self):
        return f"{self.name} {self.id} ({self.entity_type.name}/{self.entity_category.name})"


@dataclass
class Permission:
    effect: str
    permission: str

    def __post_init__(self):
        if self.permission == "FULL_CONTROL":
            self.permission = "*"


    def __str__(self):
        return f"{self.permission} ({self.effect})"



class TupleRepresentation:
    def __init__(
        self,
        source,
        source_type,
        source_id,
        permission,
        destination,
        destination_type,
        destination_id,
        mode,
    ):
        self.source = self.create_entity(
            source, source_type, source_id, EntityType.SOURCE
        )
        self.target = self.create_entity(
            destination, destination_type, destination_id, EntityType.TARGET
        )
        self.permission = self.create_permission(permission, mode)

    @staticmethod
    def create_entity(name, entity_type, entity_id, entity_category):
        entity_mapping = {
            "user": SourceType.USER,
            "group": SourceType.GROUP,
            "role": SourceType.ROLE,
            "s3": TargetType.S3,
            "postgresql": TargetType.POSTGRESQL,
        }
        entity_class = entity_mapping.get(entity_type)
        if entity_class:
            return Entity(entity_class, entity_category, name, entity_id)
        else:
            logger.error(f"Cannot parse {entity_category.name.lower()} {entity_type}")
            return None

    @staticmethod
    def create_permission(permission, mode):
        return Permission(mode, permission)
    
    @property
    def source_id(self):
        return f"__custom__id__{self.source_type}/{self.source}"

    @property
    def target_id(self):
        return f"__custom__id__{self.destination_type}/{self.destination}"

    def to_policy_document(self) -> dict:
        return {
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": self.permission.effect,
                        "Principal": {
                          "ID": f"{self.target_id}"
                        },
                        "Action": [
                            self.permission.action
                        ],
                        "Resource": f"{self.target_id}",
                    }
                ],
            },
        }


def save_generated_json(main_key, json_data, filename):
    output_directory = data_path / "toy_example" / "generated"

    file_path = output_directory / filename
    with open(file_path, "w") as json_file:
        json_file.write(json.dumps({main_key: json_data}, indent=4))


data_file = data_path / "sensitive" / "data.joblib"

data = joblib.load(data_file)

# Assuming the data is in a format that can be directly converted to a DataFrame
df = pd.DataFrame(data)

# Print the first 50 rows of the DataFrame
print(df.head(50))

policies = []
for index, row in df.iterrows():
    policies.append(
        TupleRepresentation(
            row["source"],
            row["source_type"],
            row["source_account_id"],
            row["permission"],
            row["destination"],
            row["destination_type"],
            row["destination_account_id"],
            row["mode"],
        ),
    )

# source -> target -> permissions mapping
permissions_mapping = {}

for policy in policies:
    if policy.source not in permissions_mapping:
        permissions_mapping[policy.source] = {}
    if policy.target not in permissions_mapping[policy.source]:
        permissions_mapping[policy.source][policy.target] = []

    permissions_mapping[policy.source][policy.target].append(policy.permission)


# Assuming 'permission' is one of the columns in the DataFrame
# Get unique entries in the 'permission' column
unique_permissions = pd.unique(df["permission"])

# Convert the array of unique permissions to a set
permissions_set = set(unique_permissions)

# Print the set of unique permissions
print("\n".join(permissions_set))


# TODO: Create the json structure as in "toy/example/processed
# you can use source and destination columns as ids,
# permission FULL_CONTROL = * action
# permission belongs => relates users to groups
# permission sts:AssumeRole => relates roles
# etc..
# you can use a custom utils/strings/get_name_and_type_from_id function to parse the source and destination
# and get the type (role, group etc..) and an id (e.g. identity_1) etc..


def create_jsons_from_tuple(data, output_folder):
    """Create the json structure as in "toy/example/processed"""


def get_effect(permissions):
    effects = {
        permission.effect for permission in permissions
    }  # Set comprehension to get unique effects

    if len(effects) == 1:
        return effects.pop()  # If all effects are the same, return one of them
    else:
        raise ValueError("Permissions have different effects")


# POLICIES.JSON
#
# The policies are inferred from the pairs (source, target)
all_policies = []

# user ID -> policy IDs
users_mapping = {}

for source, v in permissions_mapping.items():
    for target, permissions in v.items():
        try:
            effect = get_effect(permissions)
        except ValueError as e:
            print("Error:", e)

        # ! id cannot be inferred from the original data
        policy_id = str(uuid.uuid4())

        all_policies.append(
            {
                "PolicyDocument": {
                    "Version": "2012-10-17",  # ! this information cannot be inferred from the original data
                    "Statement": [
                        {
                            "Effect": effect,
                            "Action": [
                                permission.action for permission in permissions
                            ],
                            "Resource": f"{target.id}/{target.name}",
                        }
                    ],
                },
                "ID": policy_id,
            }
        )

        if source.id not in users_mapping:
            users_mapping[source] = set()

        users_mapping[source].add(policy_id)

save_generated_json("IdentityBasedPolicies", all_policies, "policies.json")


# USERS.JSON
#
all_users = []
for user, policy_ids in users_mapping.items():
    attached_policies = []

    for policy_id in policy_ids:
        attached_policies.append(
            {
                "ID": policy_id,
            }
        )

    all_users.append(
        {
            "AttachedPolicies": [
                attached_policies,
            ],
            "ID": f"{user.id}/{user.name}",
        }
    )

save_generated_json("Users", all_users, "users.json")

# GROUPS.JSON
#
groups_mapping = {}  # group id -> users belonging to this group
unique_groups = {
    policy.source.id
    for policy in policies
    if policy.source.entity_type == SourceType.GROUP
}

for policy in policies:
    for entity in [policy.source, policy.target]:
        if entity.entity_type != SourceType.GROUP and entity.id in unique_groups:
            groups_mapping.setdefault(entity.id, set()).add(entity)

all_groups = []
for group_id, entities in groups_mapping.items():
    # ! id cannot be inferred from the original data
    group_id = str(uuid.uuid4())

    users = [{"ID": f"{entity.id}/{entity.name}"} for entity in entities]

    attached_policies = []
    for entity in entities:
        attached_policies.extend(
            [{"ID": permission} for permission in users_mapping.get(entity, [])]
        )

    all_groups.append(
        {"Users": users, "AttachedPolicies": attached_policies, "ID": group_id}
    )


save_generated_json("Groups", all_groups, "groups.json")


# ROLES.JSON
#
unique_roles = {
    policy.source.id
    for policy in policies
    if policy.source.entity_type == SourceType.ROLE
}


all_roles = []
for policy in policies:
    if policy.source.id in unique_roles:
        # ! id cannot be inferred from the original data
        role_id = str(uuid.uuid4())

        all_roles.append(
            {
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",  # ! this information cannot be inferred from the original data
                    "Statement": [
                        {
                            "Effect": policy.permission.effect,
                            "Principal": {
                                "AWS": f"{policy.source.id}/{policy.source.name}"
                            },
                            "Action": policy.permission.action,
                        }
                    ],
                },
                "ID": role_id,
            }
        )

save_generated_json("Roles", all_roles, "roles.json")
