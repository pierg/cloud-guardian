from dataclasses import dataclass
import pandas as pd
import joblib
from cloud_guardian.utils.shared import data_path

@dataclass
class TupleEntity:
    tuple_id: str
    id: str = None
    entity_type: str = None

    def __post_init__(self):
        if self.tuple_id == "any_user":
            self.id = "*"
            self.entity_type = "user"
        elif self.tuple_id == "adminPol":
            self.tuple_id = "user__identity__admin"
            self._split_id()
        else:
            self._split_id()

    def _split_id(self):
        tuple_split = self.tuple_id.split("__")
        self.entity_type = tuple_split[0]
        self.id = f"{tuple_split[0]}_{tuple_split[2]}"

    def __hash__(self) -> int:
        return hash(self.id)
    
    @property
    def name(self):
        return self.id

@dataclass
class TuplePermission:
    source: TupleEntity
    action: str
    target: TupleEntity

    def __post_init__(self):
        if self.action == "FULL_CONTROL":
            self.action = "*"

    def to_policy_document(self) -> dict:
        return {
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"ID": self.target.id},
                    "Action": [self.action],
                    "Resource": self.source.id,
                }]
            },
        }

    def __hash__(self) -> int:
        return hash((self.source, self.action, self.target))

class Tuples:
    def __init__(self):
        self.users = {}
        self.groups = {}
        self.roles = {}
        self.resources = {}

        self.permissions = set()

        self.roles_to_policy_document = {}
        self.group_to_users = {}

    def add(self, source, action, target):
        if source.entity_type == "user":
            self.users[source.id] = source
        elif source.entity_type == "group":
            self.groups[source.id] = source
        elif source.entity_type == "role":
            self.roles[source.id] = source
        elif source.entity_type == "s3" or source.entity_type == "postgresql":
            self.resources[source.id] = source
        else:
            raise ValueError(f"Unknown entity type: {source.entity_type}")
        if action == "belongs":
            self.group_to_users.setdefault(target.id, set()).add(source.id)
        elif action == "sts:AssumeRole":
            self.roles_to_policy_document[target.id] = {
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "ID": "{source.id}"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
            }
        else:
            self.permissions.add(TuplePermission(source, action, target))

    @classmethod
    def from_df(cls, df):
        tuples_instance = cls()
        for _, row in df.iterrows():
            tuples_instance.add(
                TupleEntity(row["source"]),
                row["permission"],
                TupleEntity(row["destination"])
            )
        return tuples_instance

    
    def get_all_relationships(self, full_actions=False):
        if full_actions:
            return {(permission.source.entity_type, permission.action, permission.target.entity_type) for permission in self.permissions}
        else:
            return {(permission.source.entity_type, permission.target.entity_type) for permission in self.permissions}

    def get_all_actions_for_pair(self, source_type, target_type):
        return {permission.action for permission in self.permissions if permission.source.entity_type == source_type and permission.target.entity_type == target_type}



# Example of use
data = joblib.load(data_path / "sensitive" / "data.joblib")
df = pd.DataFrame(data)
tuples = Tuples.from_df(df)

# Print all types of relationships
for relationship in tuples.get_all_relationships():
    print(relationship)
    for action in tuples.get_all_actions_for_pair(relationship[0], relationship[1]):
        print(action)
    print("\n")


# Print all users
for user in tuples.users.values():
    print(user.id)

# Print all groups
for group in tuples.groups.values():
    print(group.id)

# # Print all roles
# for role in tuples.roles.values():
#     print(role.id)

# # Print all resources
# for resource in tuples.resources.values():
#     print(resource)

# # Print all permissions
# for permission in tuples.permissions:
#     print(permission)
#     print(permission.to_policy_document())
#     print("\n")

