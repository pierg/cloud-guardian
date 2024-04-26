import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from cloud_guardian.aws.helpers.iam.policy_management import (
    attach_policy_to_user,
    create_policy,
    get_policy_from_name,
)
from cloud_guardian.aws.helpers.iam.user_management import (
    create_user_and_access_keys,
    get_user,
)
from cloud_guardian.aws.helpers.sts.roles import assume_role
from cloud_guardian.aws.manager import AWSManager
from cloud_guardian.iam_static.model import IAMManager


@dataclass(frozen=True)
class SupportedAction(ABC):
    category: str
    description: str
    aws_action_id: str

    @abstractmethod
    def apply(self, aws_manager: AWSManager, iam_manager: IAMManager, **kwargs) -> None:
        """Apply the action directly to the IAMGraph using explicitly passed parameters."""


@dataclass(frozen=True)
class CreateUser(SupportedAction):
    category: str = "UserManagement"
    description: str = (
        "Allows creation of new IAM users which could be abused to escalate privileges."
    )
    aws_action_id: str = "iam:CreateUser"

    def apply(
        self, aws_manager: AWSManager, iam_manager: IAMManager, user_name: str
    ) -> None:
        user_info = create_user_and_access_keys(aws_manager.iam, user_name)

        iam_manager.update_node(arn=user_info["Arn"])


@dataclass(frozen=True)
class CreatePolicy(SupportedAction):
    category: str = "PolicyManagement"
    description: str = "Allows creation of new IAM policies."
    aws_action_id: str = "iam:CreatePolicy"

    def apply(
        self,
        aws_manager: AWSManager,
        iam_manager: IAMManager,
        policy_name: str,
        actions: List[str],
        resource: str = "*",
    ) -> str:

        # Construct policy document
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": actions,
                    "Resource": resource
                }
            ]
        }

        policy_arn = create_policy(aws_manager.iam, policy_name, policy_document)

        iam_manager.update_permissions_to_node(policy_arn, policy_document)

        return policy_arn


@dataclass(frozen=True)
class AttachUserPolicy(SupportedAction):
    category: str = "PolicyManagement"
    description: str = "Allows attaching policies to a user."
    aws_action_id: str = "iam:AttachUserPolicy"

    def apply(
        self,
        aws_manager: AWSManager,
        iam_manager: IAMManager,
        user_name: str,
        policy_name: str,
    ) -> None:
        policy_arn = get_policy_from_name(aws_manager.iam, policy_name)["PolicyArn"]
        attach_policy_to_user(aws_manager.iam, policy_arn, user_name)
        user_arn = get_user(aws_manager.iam, user_name)
        iam_manager.update_permissions_to_node(policy_arn, user_arn)


@dataclass(frozen=True)
class AssumeRole(SupportedAction):
    category: str = "RoleManagement"
    description: str = "Allows assuming a role."
    aws_action_id: str = "sts:AssumeRole"

    def apply(
        self,
        aws_manager: AWSManager,
        iam_manager: IAMManager,
        role_arn: str,
    ) -> None:

        role_temoporary_credentials = assume_role(aws_manager.sts, role_arn)
        aws_manager.store_credentials(role_arn, role_temoporary_credentials)
        aws_manager.set_identity(role_arn)


class SupportedActionsFactory:
    action_mapping = {
        "iam:CreateUser": CreateUser,
        "iam:CreatePolicy": CreatePolicy,
        "iam:AttachUserPolicy": AttachUserPolicy,
        "sts:AssumeRole": AssumeRole,
    }

    _instances = {}

    @classmethod
    def get_action_by_id(cls, action_id: str) -> SupportedAction:
        if action_id not in cls._instances:
            cls._instances[action_id] = cls.action_mapping[action_id]()
        return cls._instances[action_id]


def get_all_supported_actions() -> List[SupportedAction]:
    return [action_class() for action_class in SupportedAction.__subclasses__()]


supported_actions_ids = [action.aws_action_id for action in get_all_supported_actions()]
