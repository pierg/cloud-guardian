import logging
from typing import Dict, List, Optional

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.iam_model.graph.permission.actions import ActionsFactory
from cloud_guardian.iam_model.graph.permission.effects import Effect
from cloud_guardian.iam_model.graph.permission.permission import (
    PermissionFactory,
    PermissionRank,
    Permission,
)
from cloud_guardian.iam_model.graph.relationships.relationships import (
    IsPartOf,
    CanAssumeRole,
    HasPermission,
    HasPermissionToResource,
)
from collections import defaultdict
from cloud_guardian.iam_model.graph.permission.conditions import (
    SupportedCondition,
)

logger = logging.getLogger(__name__)


# TODO: modularize into simple functions that are called at initialization from json or from the dynamic model when permforming actions (e.g. adding policy to a user etc..)


# The Arn Mapper is a singleton that keeps track of the mapping
# between the arns and the permissions and resources
class ArnMapper:
    arn_to_permissions: Dict[str, set[Permission]] = {}
    arn_to_resources: Dict[str, set[Resource]] = {}

    # TODO: to remove?
    arn_to_targets: Dict[str, set[Resource]] = {}

    def __init__(self):
        self.arn_to_permissions = defaultdict(set)

    def add_resource(
        self,
        resource_name: str,
        resource_arn: str,
        resource_type: str,
        service: str,
    ):
        self.add_resource.add(
            ResourceFactory.get_or_create(
                name=resource_name,
                arn=resource_arn,
                resource_type=resource_type,
                service=service,
            )
        )

    def add_target(
        self,
        resource_arn: str,
    ):
        targets = self.arn_to_resources[resource_arn]
        for target in targets:
            self.add_resource(
                target.name, target.arn, target.resource_type, target.service
            )

    def delete_resource(self, arn: str, resource_id: str):
        resources = self.arn_to_resources.get(arn)
        if resources is not None:
            resource_to_delete = next(
                (r for r in resources if r.id == resource_id), None
            )
            if resource_to_delete is not None:
                resources.discard(resource_to_delete)
                return
            else:
                logger.warning(
                    f"cannot delete resource (resource not found): {resource_id}"
                )
        else:
            logger.warning(f"cannot delete resource (ARN not found): {arn}")

    def add_permission(
        self,
        arn: str,
        action_pattern: str,
        effect_str: str,
        conditions: List[SupportedCondition],
        rank: Optional[PermissionRank],
    ) -> None:
        permission = PermissionFactory.get_or_create(
            action=ActionsFactory.get_or_create(action_pattern),
            effect=(Effect.ALLOW if effect_str == "Allow" else Effect.DENY),
            conditions=conditions,
            rank=rank,
        )
        self.arn_to_permissions[arn].add(permission)

    def delete_permission(self, arn: str, permission_id: str):
        permissions = self.arn_to_permissions.get(arn)
        if permissions is not None:
            permission_to_delete = next(
                (p for p in permissions if p.id == permission_id), None
            )
            if permission_to_delete is not None:
                permissions.discard(permission_to_delete)
                return
            else:
                logger.warning(
                    f"cannot delete permission (permission not found): {permission_id}"
                )
        else:
            logger.warning(f"cannot delete permission (ARN not found): {arn}")

    def get_permissions(self, arn: str) -> set[Permission]:
        return set(self.arn_to_permissions.get(arn, []))

    def get_resources(self, arn: str) -> set[Resource]:
        return set(self.arn_to_resources.get(arn, []))

    def get_targets(self, arn: str) -> set[Resource]:
        return set(self.arn_to_targets.get(arn, []))


arn_mapper = ArnMapper()


def connect_graph(graph: IAMGraph, groups_data, policies_data, roles_data, users_data):
    all_identities = {
        **UserFactory._instances,
        **GroupFactory._instances,
        **RoleFactory._instances,
        **ResourceFactory._instances,
    }
    # Add nodes
    for _, node in all_identities.items():
        graph.add_node(node)

    # Extract permissions and their relationships from identity and resource policies
    # Mapping policy ARN to permissions
    for policy in policies_data.get(
        "IdentityBasedPolicies", []
    ):
        for statement in policy.get("PolicyDocument", {}).get("Statement", []):
            # targets
            target_resource = statement["Resource"]
            if target_resource == "*":
                # any target: arn is associated with all resources
                for arn in ResourceFactory._instances:
                    arn_mapper.add_target(arn)
            else:
                # specific target: arn is associated with a unique resource
                arn_mapper.add_target(target_resource)

            # permissions
            for action in statement.get("Action", []):
                arn_mapper.add_permission(
                    policy["PolicyArn"],
                    action,
                    effect_str=statement["Effect"],
                    conditions=statement.get("Condition", []),
                    rank=(
                        PermissionRank.MONADIC
                        if statement["Resource"] == "*"
                        else PermissionRank.DYADIC
                    ),
                )

    # Function to handle permission attachment
    def handle_permissions(
        identity, attached_policies, target_data=None, permission_type=None
    ):
        if permission_type is None:
            for policy_data in attached_policies:
                policy_arn = policy_data.get("PolicyArn")
                for permission in arn_mapper.get_permissions(policy_arn):
                    if permission.rank == PermissionRank.DYADIC:
                        # Attach permission to specific resources
                        for resource_arn in policy_data.get("Resources", []):
                            resource = arn_mapper.get_resources(resource_arn)

                            if not resource:
                                # catch contradiction: dyadic permission with no target
                                # (should never happen and could be the sign of a misconfiguration)
                                logger.error("a dyadic permission has no target!")

                            graph.add_relationship(
                                HasPermissionToResource(identity, resource, permission)
                            )
                    else:
                        # Attach general permissions
                        graph.add_relationship(
                            HasPermission(identity, None, permission)
                        )

        if isinstance(permission_type, IsPartOf):
            for user_data in target_data:
                user = UserFactory._instances[user_data["UserArn"]]
                graph.add_relationship(IsPartOf(user, group))

        if isinstance(permission_type, CanAssumeRole):
            role = RoleFactory.from_dict(target_data)
            graph.add_relationship(CanAssumeRole(user, role))

    # Attach policies to users, groups, and roles
    for user_data in users_data.get("Users", []):
        user = UserFactory.get_or_create(
            name=user_data["UserName"],
            arn=user_data["UserArn"],
            create_date=user_data["CreateDate"],
        )
        handle_permissions(user, user_data.get("AttachedPolicies", []))

    for group_data in groups_data.get("Groups", []):
        group = GroupFactory.get_or_create(
            name=group_data["GroupName"],
            arn=group_data["GroupArn"],
            create_date=group_data["CreateDate"],
        )
        handle_permissions(
            group, group_data.get("AttachedPolicies", []), group_data["Users"], IsPartOf
        )

    for role_data in roles_data["Roles"]:
        for statement in role_data["AssumeRolePolicyDocument"]["Statement"]:
            if statement["Effect"] == "Allow":
                principal = statement.get("Principal", {})
                if "AWS" in principal:
                    user = UserFactory.get_or_create(
                        name=extract_identifier_from_ARN(principal["AWS"]),
                        arn=principal["AWS"],
                        create_date=None,
                    )
                    handle_permissions(
                        user,
                        role_data.get("AttachedPolicies", []),
                        role_data,
                        CanAssumeRole,
                    )

    # Load and connect resource-based policies
    for resource_data in policies_data.get(
        "ResourceBasedPolicies", []
    ):
        resource = ResourceFactory.get_or_create(
            name=resource_data["ResourceName"],
            arn=resource_data["ResourceArn"],
            resource_type=resource_data["ResourceType"],
            service=resource_data["Service"],
        )
        graph.add_node(resource)  # Ensure resources are added to the graph

        arn_mapper.add_resource(
            resource_data["ResourceName"],
            resource_data["ResourceArn"],
            resource_data["ResourceType"],
            resource_data["Service"],
        )


def extract_identifier_from_ARN(arn: str) -> str:
    # Simple example, real extraction might be more complex.
    return arn.split(":")[-1]
