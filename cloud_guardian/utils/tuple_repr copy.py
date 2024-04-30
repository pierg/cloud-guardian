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
            self.tuple_id = "*"
            self.entity_type = "user"
            self.id = "*"
        elif self.tuple_id == "adminPol":
            self.tuple_id = "user__identity__admin"
            self._split_id()
        else:
            self._split_id()

    def _split_id(self):
        parts = self.tuple_id.split("__")
        if len(parts) == 3:
            self.entity_type, _, specific_id = parts
            self.id = f"{self.entity_type}_{specific_id}"

    def __hash__(self):
        return hash(self.id)

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

    def __hash__(self):
        return hash((self.source, self.action, self.target))

class Tuples:
    def __init__(self):
        self.entity_dict = {}
        self.permissions = set()

    def add(self, source, action, target):
        self._add_entity(source)
        self._add_entity(target)
        self.permissions.add(TuplePermission(source, action, target))

    def _add_entity(self, entity):
        if entity.entity_type not in self.entity_dict:
            self.entity_dict[entity.entity_type] = {}
        self.entity_dict[entity.entity_type][entity.id] = entity

    @classmethod
    def from_df(cls, df):
        instance = cls()
        for _, row in df.iterrows():
            instance.add(
                TupleEntity(row["source"]),
                row["permission"],
                TupleEntity(row["destination"])
            )
        return instance

    def get_entities_by_type(self, entity_type):
        return self.entity_dict.get(entity_type, {})

    def get_all_entity_types(self):
        return set(self.entity_dict.keys())

# Example of use
data = joblib.load(data_path / "sensitive" / "data.joblib")
df = pd.DataFrame(data)
tuples = Tuples.from_df(df)

# Access all users
all_users = tuples.get_entities_by_type("user")
for user_id, user in all_users.items():
    print(f"User ID: {user_id}, User: {user}")

# Access all groups
all_groups = tuples.get_entities_by_type("group")
for group_id, group in all_groups.items():
    print(f"Group ID: {group_id}, Group: {group}")

# Print all entity types
for entity_type in tuples.get_all_entity_types():
    print(entity_type)
