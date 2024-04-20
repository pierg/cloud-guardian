from dataclasses import dataclass
from re import A

from cloud_guardian.iam_model.graph.exceptions import ActionNotSupported


@dataclass(frozen=True)
class SupportedAction:
    id: str
    category: str
    description: str
    aws_action: str

    def __str__(self):
        return f"{self.id} ({self.category})"


@dataclass(frozen=True)
class Any(SupportedAction):
    id: str = "Any"
    category: str = "Admin"
    description: str = "Allows any action to be performed. This is a wildcard action."
    aws_action: str = "*"


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
class AssumeRole(SupportedAction):
    id: str = "AssumeRole"
    category: str = "RoleManagement"
    description: str = "Allows a user to assume a specified IAM role."
    aws_action: str = "sts:AssumeRole"

@dataclass(frozen=True)
class DeleteUser(SupportedAction):
    id: str = "DeleteUser"
    category: str = "UserManagement"
    description: str = "Allows deletion of IAM users."
    aws_action: str = "iam:DeleteUser"


class ActionFactory:
    _instances = {}
    _action_types = {
        AssumeRole.aws_action: AssumeRole,
        CopyObject.aws_action: CopyObject,
        DeleteObject.aws_action: DeleteObject,
        CreateUser.aws_action: CreateUser,
        DeleteUser.aws_action: DeleteUser,
        GetObject.aws_action: GetObject,
        PutObject.aws_action: PutObject,
        Any.aws_action: Any,
        AssumeRole.aws_action: AssumeRole,
    }

    @classmethod
    def get_or_create(cls, aws_action: str):
        if aws_action not in cls._instances:
            if aws_action in cls._action_types:
                action_class = cls._action_types[aws_action]
                cls._instances[aws_action] = action_class()
            else:
                raise ActionNotSupported(aws_action)
        return cls._instances[aws_action]
