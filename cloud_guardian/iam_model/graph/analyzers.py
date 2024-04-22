from typing import Dict, List, Set

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.helpers import extract_identifier_from_ARN
from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.user import User, UserFactory
from cloud_guardian.iam_model.graph.permission.actions import ActionFactory
from cloud_guardian.iam_model.graph.permission.effects import Effect
from cloud_guardian.iam_model.graph.permission.permission import (
    Permission,
    PermissionFactory,
)
from cloud_guardian.iam_model.graph.relationships.relationships import (
    CanAssumeRole,
    HasPermission,
    HasPermissionToResource,
    IsPartOf,
)


def connect_graph(graph: IAMGraph, data: dict):
    all_identities = {
        **UserFactory._instances,
        **GroupFactory._instances,
        **RoleFactory._instances,
        **ResourceFactory._instances,
    }
    # Add nodes
    for id, node in all_identities.items():
        graph.add_node(id, node)

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
    # TODO Refactor below:

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
                        action=ActionFactory.get_or_create(action),
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

    def add_permissions(user: User, policy_arn: str, permissions: List[Permission]):
        # TODO: refactor: the idea is to distinguish between `HasPermission` (one node) and
        # `HasPermissionToResource` (relationship between two nodes)
        # The current implementation is not optimal as the absence of target could be the
        # result of a misconfiguration

        targets = arn_to_targets.get(policy_arn, [])

        if len(targets) > 0:
            for target in targets:
                for permission in permissions:
                    graph.add_relationship(
                        HasPermissionToResource(
                            source=user, target=target, permission=permission
                        )
                    )

        else:
            for permission in permissions:
                graph.add_relationship(
                    HasPermission(source=user, target=None, permission=permission)
                )

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
        group_permissions: List[Permission] = []
        users_belonging_to_group: List[User] = []

        for group_policy in group_data["AttachedPolicies"]:
            policy_arn = group_policy["PolicyArn"]
            group_permissions.extend(
                arn_to_policies[policy_arn] if policy_arn in arn_to_policies else []
            )

        for user_data in group_data["Users"]:
            users_belonging_to_group.append(
                UserFactory._instances[user_data["UserArn"]],
            )

        # add the relationship for each user being part of the group (per permission)
        for user in users_belonging_to_group:
            add_permissions(user, policy_arn, group_permissions)
