from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Union


@dataclass
class User:
    name: str
    arn: str
    create_date: datetime

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return (self.name, self.arn, self.create_date) == (
            other.name,
            other.arn,
            other.create_date,
        )

    def __hash__(self):
        return hash((self.name, self.arn, self.create_date))

    def __str__(self):
        return (
            f"User Name: {self.name}\n"
            f"ARN: {self.arn}\n"
            f"Create Date: {self.create_date}\n"
        )

    @property
    def id(self):
        return self.arn


class UserFactory:
    _instances = {}

    @classmethod
    def get_or_create(
        cls, name: str, arn: str, create_date: Union[datetime, None] = None
    ) -> User:
        if create_date is None:
            create_date = datetime.now()
        if arn not in cls._instances:
            cls._instances[arn] = User(name=name, arn=arn, create_date=create_date)
        return cls._instances[arn]

    @classmethod
    def from_dict(cls, user_dict: Dict[str, str]) -> User:
        return cls.get_or_create(
            name=user_dict["UserName"],
            arn=user_dict["UserArn"],
            create_date=datetime.fromisoformat(user_dict["CreateDate"]),
        )
