from dataclasses import dataclass, field
import json
from typing import List
from datetime import datetime


@dataclass
class Group:
    group_name: str
    group_id: str
    arn: str
    create_date: datetime

    def __str__(self):
        return (
            f"Group Name: {self.group_name}\nGroup ID: {self.group_id}\nARN: {self.arn}\n"
            f"Create Date: {self.create_date}\n"
        )


class GroupFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, group_name, group_id, arn, create_date):
        if group_id not in cls._instances:
            cls._instances[group_id] = Group(
                group_name=group_name,
                group_id=group_id,
                arn=arn,
                create_date=create_date,
            )
        return cls._instances[group_id]

    @classmethod
    def from_dict(cls, group_dict):
        return cls.get_or_create(
            group_name=group_dict["GroupName"],
            group_id=group_dict["GroupId"],
            arn=group_dict["Arn"],
            create_date=datetime.fromisoformat(group_dict["CreateDate"]),
        )


# json_data = {
#   "Groups": [
#     {
#       "GroupName": "Developers",
#       "GroupId": "AGIDEXAMPLE1234",
#       "Arn": "arn:aws:iam::123456789012:group/Developers",
#       "CreateDate": "2020-01-02T12:00:00Z",
#       "Users": [
#         {
#           "UserName": "Alice",
#           "UserArn": "arn:aws:iam::123456789012:user/Alice"
#         },
#         {
#           "UserName": "Bob",
#           "UserArn": "arn:aws:iam::123456789012:user/Bob"
#         }
#       ],
#       "AttachedPolicies": [
#         {
#           "PolicyName": "DevS3Access",
#           "PolicyArn": "arn:aws:iam::123456789012:policy/DevS3Access"
#         }
#       ]
#     },
#     {
#       "GroupName": "Admins",
#       "GroupId": "AGIDEXAMPLE6789",
#       "Arn": "arn:aws:iam::123456789012:group/Admins",
#       "CreateDate": "2020-03-01T12:00:00Z",
#       "Users": [
#         {
#           "UserName": "Alice",
#           "UserArn": "arn:aws:iam::123456789012:user/Alice"
#         }
#       ],
#       "AttachedPolicies": [
#         {
#           "PolicyName": "AdminAccess",
#           "PolicyArn": "arn:aws:iam::aws:policy/AdminAccess"
#         }
#       ]
#     }
#   ]
# }


# for group_data in json_data["Groups"]:
#     group = GroupFactory.from_dict(group_data)
#     print(group)
