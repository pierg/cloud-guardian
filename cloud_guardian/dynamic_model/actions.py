import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

import boto3

# Assuming IAMGraph and UserFactory are correctly implemented elsewhere
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.iam_model.graph.relationships.relationships import (
    HasPermissionToResource,
)

logger = logging.getLogger(__name__)

iam = boto3.client("iam")


def generate_arn(resource_type: str, resource_name: str) -> str:
    return f"arn:aws:iam::{resource_type}/{resource_name}"


@dataclass(frozen=True)
class SupportedAction(ABC):
    category: str
    description: str
    aws_action_id: str

    @abstractmethod
    def apply(self, graph: IAMGraph, **kwargs) -> None:
        """Apply the action directly to the IAMGraph using explicitly passed parameters."""

    @abstractmethod
    def commands(self, **kwargs) -> List[str]:
        """Return the AWS CLI commands to execute this action using explicitly passed parameters."""


@dataclass(frozen=True)
class CreateUser(SupportedAction):
    category: str = "UserManagement"
    description: str = (
        "Allows creation of new IAM users which could be abused to escalate privileges."
    )
    aws_action_id: str = "iam:CreateUser"

    def apply(self, graph: IAMGraph, user_name: str) -> None:
        logger.info(f"Creating user {user_name}")
        arn = generate_arn("user", user_name)
        user = UserFactory.get_or_create(user_name, arn)
        graph.add_node(user)

    def commands(self, user_name: str) -> List[str]:
        return [
            # f"aws iam create-user --user-name {user_name}"
        ]


@dataclass(frozen=True)
class CreatePolicy(SupportedAction):
    category: str = "PolicyManagement"
    description: str = "Allows creation of new IAM policies."
    aws_action_id: str = "iam:CreatePolicy"

    def apply(
        self, graph: IAMGraph, policy_name: str, actions: List[str], resource: str = "*"
    ) -> None:
        policy_arn = generate_arn("policy", policy_name)
        policy = {
            "PolicyName": policy_name,
            "PolicyArn": policy_arn,
            "Actions": actions,
            "Resource": resource,
        }
        graph.add_node(policy)

    def commands(
        self, policy_name: str, actions: List[str], resource: str = "*"
    ) -> List[str]:
        # policy_document = json.dumps(
        #     {
        #         "Version": "2012-10-17",
        #         "Statement": [
        #             {"Effect": "Allow", "Action": actions, "Resource": resource}
        #         ],
        #     }
        # )
        return [
            # f"aws iam create-policy --policy-name {policy_name} --policy-document '{policy_document}'"
        ]


@dataclass(frozen=True)
class AttachUserPolicy(SupportedAction):
    category: str = "PolicyManagement"
    description: str = "Allows attaching policies to a user."
    aws_action_id: str = "iam:AttachUserPolicy"

    def apply(self, graph: IAMGraph, user_id: str, policy: dict) -> None:
        # is the policy already in the graph?
        policy_node = next(
            (
                node
                for node in graph.graph.nodes()
                if "PolicyArn" in node and node["PolicyArn"] == policy["PolicyArn"]
            ),
            None,
        )

        # if the policy is not already in the graph, create it
        if not policy_node:
            try:
                policy_node = iam.create_policy(
                    PolicyName=policy["PolicyName"],
                    PolicyDocument=json.dumps(policy["PolicyDocument"]),
                )
            except Exception as e:
                logger.error(f"cannot create policy: {e}")
                return

            # FIXME: a Policy class is now needed
            graph.add_node(policy_node)

        # associate user with policy
        # FIXME: rethink the relationship between user and Policy
        node = graph.get_node_by_id(user_id)
        if node:
            graph.add_relationship(HasPermissionToResource(node, policy_node))
        else:
            logger.warning(f"unable to attach user to policy: user {user_id} not found")

    def commands(self, user_name: str, policy_arn: str) -> List[str]:
        return [
            # f"aws iam attach-user-policy --user-name {user_name} --policy-arn {policy_arn}"
        ]


@dataclass(frozen=True)
class AssumeRole(SupportedAction):
    category: str = "RoleManagement"
    description: str = "Allows assuming a role."
    aws_action_id: str = "sts:AssumeRole"

    def apply(self, graph: IAMGraph, node_id: str, role_id: str) -> None:
        # TODO: Implement, use the same methods/classes used during initialization to assign permisions to users
        # Effect: the permissions associated to 'role_id' get propagated to 'node_id'
        pass

    def commands(self, node_id: str, role_id: str) -> List[str]:
        return [
            # f"aws sts assume-role --role-arn {role_name} --role-session-name ExampleSessionName"
        ]


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
