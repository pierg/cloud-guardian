from typing import Dict, List, Set, Union

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.helpers import extract_identifier_from_ARN
from cloud_guardian.iam_model.graph.identities.group import Group, GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.user import User, UserFactory
from cloud_guardian.iam_model.graph.permission.actions import ActionsFactory
from cloud_guardian.iam_model.graph.permission.effects import Effect
from cloud_guardian.iam_model.graph.permission.permission import (
    Permission,
    PermissionFactory,
    PermissionRank,
)
from cloud_guardian.iam_model.graph.relationships.relationships import (
    CanAssumeRole,
    HasPermission,
    HasPermissionToResource,
    IsPartOf,
)
from loguru import logger


def connect_graph(graph: IAMGraph, data: dict):
    all_identities = {
        **UserFactory._instances,
        **GroupFactory._instances,
        **RoleFactory._instances,
        **ResourceFactory._instances,
    }
    # Add nodes
    for id, node in all_identities.items():
        graph.add_node(node)

    # Connect "Is Part Of" relationships
    for group_data in data["groups.json"]["Groups"]:
        group = GroupFactory.from_dict(group_data)
        for user_data in group_data["Users"]:
            user = UserFactory._instances[user_data["UserArn"]]
            graph.add_relationship(IsPartOf(user, group))

    # Connect "Can Assume Role" relationships
    for role_data in data["roles.json"]["Roles"]:
        role = RoleFactory.from_dict(role_data)
        for statement in role_data["AssumeRolePolicyDocument"]["Statement"]:
            if statement["Effect"] == "Allow":
                principal = statement.get("Principal", {})
                if "AWS" in principal:
                    user = UserFactory.get_or_create(
                        name=extract_identifier_from_ARN(principal["AWS"]),
                        arn=principal["AWS"],
                        create_date=None,
                    )
                    graph.add_relationship(CanAssumeRole(user, role))

    # Connect "Has Permission To Resource" and "Has Permission" relationships

    # Mapping between ARNs and resources
    arn_to_resources: Dict[str, Set[Resource]] = {}
    for policy in data["resources_policies.json"]["ResourceBasedPolicies"]:
        arn = policy["ResourceArn"]

        arn_to_resources[arn] = ResourceFactory.get_or_create(
            name=policy["ResourceName"],
            arn=arn,
            resource_type=policy["ResourceType"],
            service=policy["Service"],
        )

    # Mapping between ARNs and targets and policies
    arn_to_targets: Dict[str, Set[Resource]] = {}

    # FIXME: transform list of permissions to a set of permissions
    # (will require to make Permission hashable)
    arn_to_policies: Dict[str, List[Permission]] = {}

    for policy in data["identities_policies.json"]["IdentityBasedPolicies"]:
        policy_arn = policy["PolicyArn"]

        for statement in policy["PolicyDocument"]["Statement"]:
            target_resource = statement["Resource"]

            # targets
            if target_resource == "*":
                for arn in ResourceFactory._instances:
                    arn_to_targets.setdefault(policy_arn, set()).add(
                        arn_to_resources[arn]
                    )
            else:
                arn_to_targets.setdefault(policy_arn, set()).add(arn_to_resources[arn])

            # policies

            for action in statement["Action"]:
                arn_to_policies.setdefault(policy_arn, []).append(
                    PermissionFactory.get_or_create(
                        rank=(
                            # any target: monadic permission
                            # specific target: dyadic permission
                            PermissionRank.MONADIC
                            if target_resource == "*"
                            else PermissionRank.DYADIC
                        ),
                        action=ActionsFactory.get_or_create(action),
                        effect=(
                            Effect.ALLOW
                            if statement["Effect"] == "Allow"
                            else Effect.DENY
                        ),
                        conditions=(
                            statement["Condition"] if "Condition" in statement else []
                        ),
                    )
                )

    def add_permissions(
        user: Union[User, Group], policy_arn: str, permissions: List[Permission]
    ):
        for permission in permissions:
            if permission.rank is PermissionRank.MONADIC:
                graph.add_relationship(
                    HasPermission(source=user, target=None, permission=permission)
                )
            elif permission.rank is PermissionRank.DYADIC:
                targets = arn_to_targets.get(policy_arn, [])

                # catch contradiction: dyadic permission with no target
                # (should never happen and could be the sign of a misconfiguration)
                if len(targets) == 0:
                    logger.error("a dyadic permission has no target!")

                for target in targets:
                    graph.add_relationship(
                        HasPermissionToResource(
                            source=user, target=target, permission=permission
                        )
                    )
            else:
                logger.error(f"unknown permission rank: {permission.rank}")

    # Users permissions
    for user_data in data["users.json"]["Users"]:
        user = UserFactory.get_or_create(
            name=user_data["UserName"],
            arn=user_data["UserArn"],
            create_date=user_data["CreateDate"],
        )

        for policy_data in user_data["AttachedPolicies"]:
            policy_arn = policy_data["PolicyArn"]
            permissions = (
                arn_to_policies[policy_arn] if policy_arn in arn_to_policies else []
            )
            add_permissions(user, policy_arn, permissions)

    # Groups
    for group_data in data["groups.json"]["Groups"]:
        group = GroupFactory.get_or_create(
            name=group_data["GroupName"],
            arn=group_data["GroupArn"],
            create_date=group_data["CreateDate"],
        )

        for group_policy in group_data["AttachedPolicies"]:
            add_permissions(
                group,
                group_policy["PolicyArn"],
                arn_to_policies[policy_arn] if policy_arn in arn_to_policies else [],
            )
