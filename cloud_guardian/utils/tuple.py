from cloud_guardian.utils.shared import data_path
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import json
from enum import Enum
from cloud_guardian import logger
from cloud_guardian.iam_static.graph.permission.effects import Effect
import uuid


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


class Permission:
    def __init__(self, effect, permission):
        self.effect = effect
        self.permission = permission

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
        source_mapping = {
            "user": SourceType.USER,
            "group": SourceType.GROUP,
            "role": SourceType.ROLE,
        }
        self.source = (
            Entity(
                source_mapping.get(source_type), EntityType.SOURCE, source, source_id
            )
            if source_type in source_mapping
            else logger.error(f"cannot parse source {source_type}")
        )

        target_mapping = {
            "s3": TargetType.S3,
            "postgresql": TargetType.POSTGRESQL,
        }

        target_mapping.update(source_mapping)

        self.target = (
            Entity(
                target_mapping.get(destination_type),
                EntityType.TARGET,
                destination,
                destination_id,
            )
            if destination_type in target_mapping
            else logger.error(f"cannot parse target {destination_type}")
        )

        self.permission = Permission(
            Effect.ALLOW if mode == "allow" else Effect.DENY,
            permission,
        )


def save_generated_json(main_key, json_data, filename):
    output_directory = data_path / "toy_example" / "generated"

    file_path = output_directory / filename
    with open(file_path, "w") as json_file:
        json_file.write(json.dumps({main_key: json_data}, indent=4))


data_file = data_path / "sensitive" / "ds_4_tuples.joblib"

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

# groups
groups_mapping = {}  # group id -> users belonging to this group
unique_groups = [
    policy for policy in policies if policy.source.entity_type == SourceType.GROUP
]
for policy in policies:
    policy_id = policy.source.id
    for group in unique_groups:
        if policy_id in group.source.id:
            groups_mapping.setdefault(group.source.id, set()).add(policy.source)
        if policy_id in group.target.id:
            groups_mapping.setdefault(group.target.id, set()).add(policy.source)


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

        policy_id = str(uuid.uuid4())  # ! id cannot be inferred from the original data

        all_policies.append(
            {
                "PolicyDocument": {
                    "Version": "2012-10-17",  # ! this information cannot be inferred from the original data
                    "Statement": [
                        {
                            "Effect": effect.value,
                            "Action": [
                                [permission.permission for permission in permissions],
                            ],
                            "Resource": f"{target.id}/{target.name}",
                        }
                    ],
                },
                "ID": policy_id,
            }
        )

        if source.id not in users_mapping:
            users_mapping[source] = []

        users_mapping[source].append(policy_id)

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
