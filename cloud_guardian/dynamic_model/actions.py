import re
from dataclasses import dataclass

from cloud_guardian.iam_model.graph.exceptions import ActionNotSupported
from cloud_guardian.iam_model.graph.helpers import extract_identifier_from_ARN


@dataclass(frozen=True)
class SupportedAction:
    id: str
    category: str
    description: str
    aws_action: str

    def __str__(self):
        return f"{self.id} ({self.category})"
    

@dataclass(frozen=True)
class AssumeRole(SupportedAction):
    id: str = "AssumeRole"
    category: str = "RoleManagement"
    description: str = "Allows a user to assume a specified IAM role."
    aws_action: str = "sts:AssumeRole"


@dataclass(frozen=True)
class GetObject(SupportedAction):
    id: str = "GetObject"
    category: str = "DataManagement"
    description: str = "Allows reading an object from S3."
    aws_action: str = "s3:GetObject"



@dataclass(frozen=True)
class PutObject(SupportedAction):
    id: str = "PutObject"
    category: str = "DataManagement"
    description: str = "Allows writing an object to S3."
    aws_action: str = "s3:PutObject"


@dataclass(frozen=True)
class CopyObject(SupportedAction):
    id: str = "CopyObject"
    category: str = "DataManagement"
    description: str = "Allows copying objects within S3 from one location to another."
    aws_action: str = "s3:CopyObject"


@dataclass(frozen=True)
class DeleteObject(SupportedAction):
    id: str = "DeleteObject"
    category: str = "DataManagement"
    description: str = (
        "Allows deleting an object in S3. Used together with CopyObject to simulate moving an object."
    )
    aws_action: str = "s3:DeleteObject"


@dataclass(frozen=True)
class CreateUser(SupportedAction):
    id: str = "CreateUser"
    category: str = "UserManagement"
    description: str = (
        "Allows creation of new IAM users which could be abused to escalate privileges."
    )
    aws_action: str = "iam:CreateUser"


@dataclass(frozen=True)
class DeleteUser(SupportedAction):
    id: str = "DeleteUser"
    category: str = "UserManagement"
    description: str = "Allows deletion of IAM users."
    aws_action: str = "iam:DeleteUser"

