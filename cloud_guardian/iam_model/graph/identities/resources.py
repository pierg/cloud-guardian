from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Resource:
    resource_name: str
    resource_arn: str
    service: str
    resource_type: str

    def __str__(self):
        return (
            f"Resource Name: {self.resource_name}, ARN: {self.resource_arn}, "
            f"Service: {self.service}, Resource Type: {self.resource_type}\n"
        )

    @property
    def id(self):
        return self.resource_arn


class ResourceFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, resource_name, resource_arn, service, resource_type):
        if resource_arn not in cls._instances:
            cls._instances[resource_arn] = Resource(
                resource_name=resource_name,
                resource_arn=resource_arn,
                service=service,
                resource_type=resource_type,
            )
        return cls._instances[resource_arn]

    @classmethod
    def from_dict(cls, resource_dict):
        resource_name = resource_dict["ResourceName"]
        resource_arn = resource_dict["ResourceArn"]
        service = resource_dict["Service"]
        resource_type = resource_dict["ResourceType"]
        return cls.get_or_create(resource_name, resource_arn, service, resource_type)


# json_data = {
#   "ResourceBasedPolicies": [
#     {
#       "ResourceName": "example-bucket",
#       "ResourceArn": "arn:aws:s3:::example-bucket",
#       "Service": "Amazon S3",
#       "ResourceType": "Bucket",
#       "PolicyDocument": {
#         "Version": "2012-10-17",
#         "Statement": [
#           {
#             "Effect": "Allow",
#             "Principal": {
#               "AWS": [
#                 "arn:aws:iam::123456789012:user/Alice",
#                 "arn:aws:iam::123456789012:user/Bob"
#               ]
#             },
#             "Action": "s3:GetObject",
#             "Resource": "arn:aws:s3:::example-bucket/*",
#             "Condition": {
#               "DateGreaterThan": {
#                 "aws:CurrentTime": "2023-01-01T00:00:00Z"
#               },
#               "DateLessThan": {
#                 "aws:CurrentTime": "2023-12-31T23:59:59Z"
#               }
#             }
#           }
#         ]
#       }
#     },
#     {
#       "ResourceName": "dev-database",
#       "ResourceArn": "arn:aws:dynamodb:us-west-2:123456789012:table/dev-database",
#       "Service": "Amazon DynamoDB",
#       "ResourceType": "Table",
#       "PolicyDocument": {
#         "Version": "2012-10-17",
#         "Statement": [
#           {
#             "Effect": "Allow",
#             "Principal": {
#               "AWS": [
#                 "arn:aws:iam::123456789012:role/EC2Role",
#                 "arn:aws:iam::123456789012:role/DataAnalyticsRole"
#               ]
#             },
#             "Action": [
#               "dynamodb:Query",
#               "dynamodb:Scan"
#             ],
#             "Resource": "arn:aws:dynamodb:us-west-2:123456789012:table/dev-database",
#             "Condition": {
#               "ForAllValues:StringEquals": {
#                 "dynamodb:LeadingKeys": ["${aws:username}"]
#               }
#             }
#           }
#         ]
#       }
#     }
#   ]
# }

# for resource_data in json_data["ResourceBasedPolicies"]:
#     resource = ResourceFactory.from_dict(resource_data)
#     print(resource)
