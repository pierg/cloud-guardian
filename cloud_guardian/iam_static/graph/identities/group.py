from dataclasses import dataclass
from datetime import datetime


@dataclass
class Group:
    name: str
    arn: str
    create_date: datetime

    def __str__(self):
        return (
            f"Group Name: {self.name}\n\nARN: {self.arn}\n"
            f"Create Date: {self.create_date}\n"
        )

    @property
    def id(self):
        return self.arn


class GroupFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, name, arn, create_date):
        if arn not in cls._instances:
            cls._instances[arn] = Group(
                name=name,
                arn=arn,
                create_date=create_date,
            )
        return cls._instances[arn]

    @classmethod
    def from_dict(cls, group_dict):
        return cls.get_or_create(
            name=group_dict["GroupName"],
            arn=group_dict["GroupArn"],
            create_date=datetime.fromisoformat(group_dict["CreateDate"]),
        )
