from dataclasses import dataclass



@dataclass(frozen=True)
class SupportedAction:
    category: str
    description: str
    aws_action_id: str

    def __str__(self):
        return f"{self.id} ({self.category})"


@dataclass(frozen=True)
class AssumeRole(SupportedAction):
    category: str = "RoleManagement"
    description: str = "Allows a user to assume a specified IAM role."
    aws_action_id: str = "sts:AssumeRole"


@dataclass(frozen=True)
class GetObject(SupportedAction):
    category: str = "DataManagement"
    description: str = "Allows reading an object from S3."
    aws_action_id: str = "s3:GetObject"


@dataclass(frozen=True)
class PutObject(SupportedAction):
    category: str = "DataManagement"
    description: str = "Allows writing an object to S3."
    aws_action_id: str = "s3:PutObject"


@dataclass(frozen=True)
class CopyObject(SupportedAction):
    category: str = "DataManagement"
    description: str = "Allows copying objects within S3 from one location to another."
    aws_action_id: str = "s3:CopyObject"


@dataclass(frozen=True)
class DeleteObject(SupportedAction):
    category: str = "DataManagement"
    description: str = (
        "Allows deleting an object in S3. Used together with CopyObject to simulate moving an object."
    )
    aws_action_id: str = "s3:DeleteObject"


@dataclass(frozen=True)
class CreateUser(SupportedAction):
    category: str = "UserManagement"
    description: str = (
        "Allows creation of new IAM users which could be abused to escalate privileges."
    )
    aws_action_id: str = "iam:CreateUser"


@dataclass(frozen=True)
class DeleteUser(SupportedAction):
    id: str = "DeleteUser"
    category: str = "UserManagement"
    description: str = "Allows deletion of IAM users."
    aws_action_id: str = "iam:DeleteUser"


def get_all_supported_actions() -> list[SupportedAction]:
    return [action_class() for action_class in SupportedAction.__subclasses__()]
