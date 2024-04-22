from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class User:
    user_name: str
    arn: str
    create_date: datetime

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return (self.user_name, self.arn, self.create_date) == (
            other.user_name,
            other.arn,
            other.create_date,
        )

    def __hash__(self):
        return hash((self.user_name, self.arn, self.create_date))

    def __str__(self):
        return (
            f"User Name: {self.user_name}\n"
            f"ARN: {self.arn}\n"
            f"Create Date: {self.create_date}\n"
        )

    @property
    def id(self):
        return self.arn


class UserFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, user_name: str, arn: str, create_date: datetime) -> User:
        if arn not in cls._instances:
            cls._instances[arn] = User(
                user_name=user_name, arn=arn, create_date=create_date
            )
        return cls._instances[arn]

    @classmethod
    def from_dict(cls, user_dict: Dict[str, str]) -> User:
        return cls.get_or_create(
            user_name=user_dict["UserName"],
            arn=user_dict["Arn"],
            create_date=datetime.fromisoformat(user_dict["CreateDate"]),
        )


# json_data = {
#     "Users": [
#       {
#         "UserName": "Alice",
#         "UserId": "AIDAEXAMPLE1234",
#         "Arn": "arn:aws:iam::123456789012:user/Alice",
#         "CreateDate": "2020-01-01T12:00:00Z",
#         "AttachedPolicies": [
#           {
#             "PolicyName": "AdminAccess",
#             "PolicyArn": "arn:aws:iam::aws:policy/AdminAccess"
#           }
#         ]
#       },
#       {
#         "UserName": "Bob",
#         "UserId": "BIDEXAMPLE5678",
#         "Arn": "arn:aws:iam::123456789012:user/Bob",
#         "CreateDate": "2020-01-15T12:00:00Z",
#         "AttachedPolicies": [
#           {
#             "PolicyName": "ReadOnlyAccess",
#             "PolicyArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"
#           }
#         ]
#       }
#     ]
#   }


# for user_data in json_data["Users"]:
#     user = UserFactory.get_or_create(user_name=user_data["UserName"],
#                                      user_id=user_data["UserId"],
#                                      arn=user_data["Arn"],
#                                      create_date=datetime.fromisoformat(user_data["CreateDate"]))

# for user in UserFactory._instances.values():
#     print(user)
