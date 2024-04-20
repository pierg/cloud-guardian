import json
from typing import Union, List, Dict, Set

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.helpers import (
    extract_identifier_from_ARN,
)
from cloud_guardian.iam_model.graph.identities import user
from cloud_guardian.iam_model.graph.identities.group import Group, GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_model.graph.identities.role import Role, RoleFactory
from cloud_guardian.iam_model.graph.identities.services import (
    ServiceFactory,
    SupportedService,
)
from cloud_guardian.iam_model.graph.identities.user import User, UserFactory
from cloud_guardian.iam_model.graph.permission.permission import (
    PermissionFactory,
    Permission,
)

from cloud_guardian.iam_model.graph.relationships.relationships import (
    IsPartOf,
    CanAssumeRole,
    HasPermission,
)
from cloud_guardian.iam_model.graph.permission.actions import (
    ActionFactory,
)
from cloud_guardian.utils.shared import aws_example_folder
from cloud_guardian.iam_model.graph.permission.effects import Effect


from loguru import logger

data_folder = aws_example_folder

# Create a dictionary to hold the data from each JSON file
data = {}
json_files = [
    "groups.json",
    "identities_policies.json",
    "resources_policies.json",
    "roles.json",
    "users.json",
]
for file_name in json_files:
    file_path = data_folder / file_name
    with open(file_path, "r") as file:
        data[file_name] = json.load(file)

# Parse identities

# FIXME: do not necessarily contain all users
# (see for instance: `roles.json` -> `arn:aws:iam::123456789012:root`)
# I would therefore recommend to parse _all_ files to detect all users
# to detect potential misconfigurations
for user_data in data["users.json"]["Users"]:
    UserFactory.from_dict(user_data)

for group_data in data["groups.json"]["Groups"]:
    GroupFactory.from_dict(group_data)

for role_data in data["roles.json"]["Roles"]:
    RoleFactory.from_dict(role_data)

for resource_data in data["resources_policies.json"]["ResourceBasedPolicies"]:
    ResourceFactory.from_dict(resource_data)

for role_data in data["roles.json"]["Roles"]:
    for statement in role_data["AssumeRolePolicyDocument"]["Statement"]:
        if "Service" in statement["Principal"]:
            service_principal = statement["Principal"]["Service"]
            ServiceFactory.get_or_create(service_principal)

all_identities: dict[str, Union[User, Group, Role, Resource, SupportedService]] = {
    **UserFactory._instances,
    **GroupFactory._instances,
    **RoleFactory._instances,
    **ResourceFactory._instances,
    **ServiceFactory._instances,
}

print(list(all_identities.keys()))

graph = IAMGraph()

# Add nodes to the graph
for id, node in all_identities.items():
    graph.add_node(id, node)


# Parse relationships
for group_data in data["groups.json"]["Groups"]:
    group = GroupFactory.from_dict(group_data)
    for user_data in group_data["Users"]:
        user = UserFactory._instances[user_data["UserArn"]]
        graph.add_relationship(IsPartOf(user, group))


# Can Assume Role relationships
for role_data in data["roles.json"]["Roles"]:
    role = RoleFactory.from_dict(role_data)
    for statement in role_data["AssumeRolePolicyDocument"]["Statement"]:
        if statement["Effect"] != "Allow":
            continue

        user = UserFactory.get_or_create(
            user_name=extract_identifier_from_ARN(statement["Principal"]["AWS"]),
            arn=statement["Principal"]["AWS"],
            create_date=None,  # FIXME: cannot infer user creation date from roles.json
        )

        graph.add_relationship(CanAssumeRole(user, role))
        logger.info(
            f"added relationship between {user.user_name} and role {role.role_name}: can assume role"
        )

# mapping between permissions (ARN) and targets
# TODO: process resources_policies.json
permissions_to_targets: Dict[str, Set[Resource]] = {}
for policy in data["identities_policies.json"]["IdentityBasedPolicies"]:
    arn = policy["PolicyArn"]

    for statement in policy["PolicyDocument"]["Statement"]:
        target_resource = statement["Resource"]

        if target_resource == "*":
            for resource in ResourceFactory._instances:
                permissions_to_targets.setdefault(arn, set()).add(
                    ResourceFactory.get_or_create(
                        resource_name=extract_identifier_from_ARN(
                            resource
                        ),  # TODO: refactor to extract it from resources_policies.json
                        resource_arn=resource,
                        service=None,  # TODO: refactor to extract it from resources_policies.json
                        resource_type=None,  # TODO: refactor to extract it from resources_policies.json
                    )
                )
        else:
            permissions_to_targets.setdefault(arn, set()).add(
                ResourceFactory.get_or_create(
                    resource_name=extract_identifier_from_ARN(
                        target_resource
                    ),  # TODO: refactor to extract it from resources_policies.json
                    resource_arn=target_resource,
                    service=None,  # TODO: refactor to extract it from resources_policies.json
                    resource_type=None,  # TODO: refactor to extract it from resources_policies.json)
                )
            )


# Users permissions
for user_data in data["users.json"]["Users"]:
    user = UserFactory.get_or_create(
        user_name=user_data["UserName"],
        arn=user_data["Arn"],
        create_date=user_data["CreateDate"],
    )
    for policy_data in user_data["AttachedPolicies"]:
        arn = policy_data["PolicyArn"]
        policy = extract_identifier_from_ARN(arn)

        permission = PermissionFactory.get_or_create(
            action=ActionFactory.get_or_create(arn),
            effect=Effect(
                Effect.ALLOW
            ),  # NOTE: do we assume all permissions ALLOW by default?
            conditions=[],
        )

        for target in permissions_to_targets.get(arn, []):
            graph.add_relationship(
                HasPermission(user, target=target, permission=permission)
            )
            logger.info(
                f"added relationship between {user.user_name} and {target.resource_name}: {permission.action} [{permission.effect}]"
            )

# Groups
for group_data in data["groups.json"]["Groups"]:
    permissions: List[Permission] = []
    users_belonging_to_group: List[User] = []

    for group_policy in group_data["AttachedPolicies"]:
        arn = group_policy["PolicyArn"]
        permission = PermissionFactory.get_or_create(
            action=ActionFactory.get_or_create(arn),
            effect=Effect(
                Effect.ALLOW
            ),  # NOTE: do we assume all permissions ALLOW by default?
            conditions=[],
        )
        permissions.append(permission)

    for user_data in group_data["Users"]:
        users_belonging_to_group.append(
            UserFactory._instances[user_data["UserArn"]],
        )

    # add the relationship for each user being part of the group (per permission)
    for user in users_belonging_to_group:
        for permission in permissions:
            for target in permissions_to_targets.get(arn, []):
                graph.add_relationship(
                    HasPermission(user, target=target, permission=permission)
                )
                logger.info(
                    f"added relationship between {user.user_name} (as part of group {group_data['GroupName']}) and {target.resource_name}: {permission.action} [{permission.effect}]"
                )


# Permissions can be instantiated and retried from the "Statement" filed in the jsons, e.g. :
# I'm not sure if to instantiate them first like with identities, or as we parse relationships, ultimately is the same as they are singletons

permission_data = {
    "Effect": "Allow",
    "Action": ["sts:AssumeRole", "s3:CopyObject"],
    "Principal": {
        "AWS": [
            "arn:aws:iam::123456789012:user/Alice",
            "arn:aws:iam::123456789012:user/Bob",
        ]
    },
    "Condition": {
        "DateGreaterThan": {"aws:CurrentTime": "2023-01-01T00:00:00Z"},
        "IpAddress": {"aws:SourceIp": "203.0.113.0/24"},
    },
    "Resource": "arn:aws:s3:::example-bucket/*",
}

permissions = PermissionFactory.from_dict(permission_data)
for perm in permissions:
    print(perm)
