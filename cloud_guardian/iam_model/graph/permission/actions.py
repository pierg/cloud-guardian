from dataclasses import dataclass

# Define the base class for supported actions
@dataclass(frozen=True)
class SupportedAction:
    id: str
    category: str
    description: str
    aws_action: str

    def __str__(self):
        return (f"{self.id} ({self.category})")

@dataclass(frozen=True)
class AssumeRole(SupportedAction):
    id: str = "AssumeRole"
    category: str = "RoleManagement"
    description: str = "Allows a user to assume a specified IAM role."
    aws_action: str = "sts:AssumeRole"

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
    description: str = "Allows deleting an object in S3. Used together with CopyObject to simulate moving an object."
    aws_action: str = "s3:DeleteObject"

@dataclass(frozen=True)
class CreateUser(SupportedAction):
    id: str = "CreateUser"
    category: str = "UserManagement"
    description: str = "Allows creation of new IAM users which could be abused to escalate privileges."
    aws_action: str = "iam:CreateUser"

# Factory class to manage and instantiate actions
class ActionFactory:
    _instances = {}
    _action_types = {
        AssumeRole.aws_action: AssumeRole,
        CopyObject.aws_action: CopyObject,
        DeleteObject.aws_action: DeleteObject,
        CreateUser.aws_action: CreateUser,
    }

    @classmethod
    def get_action(cls, aws_action):
        if aws_action not in cls._instances:
            if aws_action in cls._action_types:
                action_class = cls._action_types[aws_action]
                cls._instances[aws_action] = action_class()
            else:
                raise ValueError(f"Action '{aws_action}' is not supported.")
        return cls._instances[aws_action]
