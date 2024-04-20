from dataclasses import dataclass
from datetime import datetime


@dataclass
class Role:
    role_name: str
    role_id: str
    arn: str
    create_date: datetime

    def __str__(self):
        return (
            f"Role Name: {self.role_name}\nRole ID: {self.role_id}\nARN: {self.arn}\n"
        )

    @property
    def id(self):
        return self.arn


class RoleFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, role_name, role_id, arn, create_date):
        if role_id not in cls._instances:
            cls._instances[role_id] = Role(
                role_name=role_name,
                role_id=role_id,
                arn=arn,
                create_date=create_date,
            )
        return cls._instances[role_id]

    @classmethod
    def from_dict(cls, role_dict):
        role_name = role_dict["RoleName"]
        role_id = role_dict["RoleId"]
        arn = role_dict["Arn"]
        create_date = datetime.fromisoformat(role_dict["CreateDate"])
        return cls.get_or_create(role_name, role_id, arn, create_date)


# json_data = {
#   "Roles": [
#     {
#       "RoleName": "EC2Role",
#       "RoleId": "ARIDEXAMPLE1234",
#       "Arn": "arn:aws:iam::123456789012:role/EC2Role",
#       "CreateDate": "2020-01-03T12:00:00Z",
#       "AssumeRolePolicyDocument": {
#         "Version": "2012-10-17",
#         "Statement": [
#           {
#             "Effect": "Allow",
#             "Principal": {
#               "Service": "ec2.amazonaws.com",
#               "AWS": "arn:aws:iam::123456789012:user/Alice"
#             },
#             "Action": "sts:AssumeRole"
#           }
#         ]
#       }
#     },
#     {
#       "RoleName": "LambdaExecutionRole",
#       "RoleId": "ARIDEXAMPLE5678",
#       "Arn": "arn:aws:iam::123456789012:role/LambdaExecutionRole",
#       "CreateDate": "2020-02-03T12:00:00Z",
#       "AssumeRolePolicyDocument": {
#         "Version": "2012-10-17",
#         "Statement": [
#           {
#             "Effect": "Allow",
#             "Principal": {
#               "Service": "lambda.amazonaws.com",
#               "Federated": "cognito-identity.amazonaws.com",
#               "AWS": "arn:aws:iam::123456789012:root"
#             },
#             "Action": "sts:AssumeRole"
#           }
#         ]
#       }
#     }
#   ]
# }


# for role_data in json_data["Roles"]:
#     role = RoleFactory.from_dict(role_data)
#     print(role)
