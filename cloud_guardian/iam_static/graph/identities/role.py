from dataclasses import dataclass
from datetime import datetime


@dataclass
class Role:
    name: str
    arn: str
    create_date: datetime

    def __eq__(self, other):
        if not isinstance(other, Role):
            return False
        return (self.name, self.arn, self.create_date) == (
            other.name,
            other.arn,
            other.create_date,
        )

    def __hash__(self):
        return hash((self.name, self.arn, self.create_date))

    def __str__(self):
        return f"Role Name: {self.name}\nRole ID: {self.role_id}\nARN: {self.arn}\n"

    @property
    def id(self):
        return self.arn


class RoleFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, name, arn, create_date):
        if arn not in cls._instances:
            cls._instances[arn] = Role(
                name=name,
                arn=arn,
                create_date=create_date,
            )
        return cls._instances[arn]

    @classmethod
    def from_dict(cls, role_dict):
        name = role_dict["RoleName"]
        arn = role_dict["RoleArn"]
        create_date = datetime.fromisoformat(role_dict["CreateDate"])
        return cls.get_or_create(name, arn, create_date)
