import logging

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.helpers import extract_identifier_from_ARN
from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import ResourceFactory
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.iam_model.graph.permission.actions import ActionsFactory
from cloud_guardian.iam_model.graph.permission.effects import Effect
from cloud_guardian.iam_model.graph.permission.permission import (
    PermissionFactory,
    PermissionRank,
)
from cloud_guardian.iam_model.graph.relationships.relationships import (
    HasPermission,
    HasPermissionToResource,
)
from loguru import logger

logger = logging.getLogger(__name__)


def connect_graph(graph: IAMGraph, data: dict):
    # TODO: check / refactor / compare with analyzers_old.py

    all_identities = {
        **UserFactory._instances,
        **GroupFactory._instances,
        **RoleFactory._instances,
        **ResourceFactory._instances,
    }
    # Add nodes
    for id, node in all_identities.items():
        graph.add_node(node)

    # Extract permissions and their relationships from identity and resource policies
    arn_to_permissions = {}  # Mapping policy ARN to permissions
    for policy in data.get("identities_policies.json", {}).get(
        "IdentityBasedPolicies", []
    ):
        for statement in policy.get("PolicyDocument", {}).get("Statement", []):
            permissions = [
                PermissionFactory.get_or_create(
                    rank=(
                        PermissionRank.MONADIC
                        if statement["Resource"] == "*"
                        else PermissionRank.DYADIC
                    ),
                    action=ActionsFactory.get_or_create(action),
                    effect=(
                        Effect.ALLOW if statement["Effect"] == "Allow" else Effect.DENY
                    ),
                    conditions=statement.get("Condition", []),
                )
                for action in statement.get("Action", [])
            ]
            arn_to_permissions[policy["PolicyArn"]] = permissions

    # Function to handle permission attachment
    def handle_permissions(identity, attached_policies):
        for policy_data in attached_policies:
            policy_arn = policy_data.get("PolicyArn")
            permissions = arn_to_permissions.get(policy_arn, [])
            for permission in permissions:
                if permission.rank == PermissionRank.DYADIC:
                    # Attach permission to specific resources
                    for resource_arn in policy_data.get("Resources", []):
                        resource = ResourceFactory.get_or_create(arn=resource_arn)
                        graph.add_relationship(
                            HasPermissionToResource(identity, resource, permission)
                        )
                else:
                    # Attach general permissions
                    graph.add_relationship(HasPermission(identity, None, permission))

    # Attach policies to users and roles
    for user_data in data.get("users.json", {}).get("Users", []):
        user = UserFactory.get_or_create(
            name=user_data["UserName"],
            arn=user_data["UserArn"],
            create_date=user_data["CreateDate"],
        )
        handle_permissions(user, user_data.get("AttachedPolicies", []))

    for group_data in data.get("groups.json", {}).get("Groups", []):
        group = GroupFactory.get_or_create(
            name=group_data["GroupName"],
            arn=group_data["GroupArn"],
            create_date=group_data["CreateDate"],
        )
        handle_permissions(group, group_data.get("AttachedPolicies", []))

    # Load and connect resource-based policies
    for resource_data in data.get("resources_policies.json", {}).get(
        "ResourceBasedPolicies", []
    ):
        resource = ResourceFactory.get_or_create(
            name=resource_data["ResourceName"],
            arn=resource_data["ResourceArn"],
            resource_type=resource_data["ResourceType"],
            service=resource_data["Service"],
        )
        graph.add_node(resource)  # Ensure resources are added to the graph


def extract_identifier_from_ARN(arn: str) -> str:
    # Simple example, real extraction might be more complex.
    return arn.split(":")[-1]
