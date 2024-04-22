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
class Any(SupportedAction):
    id: str = "Any"
    category: str = "Admin"
    description: str = "Allows any action to be performed. This is a wildcard action."
    aws_action: str = "*"


@dataclass(frozen=True)
class Admin(SupportedAction):
    id: str = "AdminAccess"
    category: str = "Admin"
    description: str = (
        "Grants full administrative access to AWS resources for a specified IAM role."
    )
    aws_action: str = "AdminAccess"


@dataclass(frozen=True)
class ReadOnly(SupportedAction):
    id: str = "ReadOnlyAccess"
    category: str = "DataManagement"
    description: str = "Grants read-only access to various AWS resources and services."
    aws_action: str = "ReadOnlyAccess"


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
class DevS3Access(SupportedAction):
    id: str = "DevS3Access"
    category: str = "DataManagement"
    description: str = (
        "Allows accessing an object from S3 in a development environment."
    )
    aws_action: str = "s3:DevS3Access"


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


def is_supported_action(action, action_types):
    return action == "*" or any(
        re.search(action, action_type, re.IGNORECASE) for action_type in action_types
    )


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
        # NOTE: should all actions be defined and listed in the code?
        DevS3Access.aws_action: DevS3Access,
        ReadOnly.aws_action: ReadOnly,
        Admin.aws_action: Admin,
    }

    def get_action(cls, aws_action: str) -> SupportedAction:
        if aws_action in cls._action_types:
            return cls._action_types[aws_action]
        else:
            # TODO: improve the implementation to make it
            # more robust (the idea is to identify the relevant
            # action when the `_action_types` object does not
            # strictly contains the aws_action name)
            for k, v in cls._action_types.items():
                if re.search(aws_action, k, re.IGNORECASE):
                    return v

        raise ActionNotSupported(aws_action)

    @classmethod
    def get_or_create(cls, aws_action: str) -> SupportedAction:
        aws_action = extract_identifier_from_ARN(aws_action)
        if aws_action not in cls._instances:
            # TODO: should be refactor to properly support wildcards
            # and the different IAM policy formats
            if is_supported_action(aws_action, cls._action_types):
                action_class = cls.get_action(cls, aws_action)
                cls._instances[aws_action] = action_class()
            else:
                raise ActionNotSupported(aws_action)
        return cls._instances[aws_action]
