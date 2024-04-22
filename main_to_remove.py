import json
from typing import Dict, List, Set, Union

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.helpers import extract_identifier_from_ARN
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
from cloud_guardian.iam_model.graph.permission.actions import ActionFactory
from cloud_guardian.iam_model.graph.permission.effects import Effect
from cloud_guardian.iam_model.graph.permission.permission import (
    Permission,
    PermissionFactory,
)
from cloud_guardian.iam_model.graph.plotting import save_graph_pdf
from cloud_guardian.iam_model.graph.relationships.relationships import (
    CanAssumeRole,
    HasPermission,
    HasPermissionToResource,
    IsPartOf,
)
from cloud_guardian.utils.shared import aws_example_folder, output_path
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
            name=extract_identifier_from_ARN(statement["Principal"]["AWS"]),
            arn=statement["Principal"]["AWS"],
            create_date=None,  # FIXME: cannot infer user creation date from roles.json
        )

        graph.add_relationship(CanAssumeRole(user, role))

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
                arn_to_targets.setdefault(policy_arn, set()).add(arn_to_resources[arn])
        else:
            arn_to_targets.setdefault(policy_arn, set()).add(arn_to_resources[arn])

        # policies
        for action in statement["Action"]:
            arn_to_policies.setdefault(policy_arn, []).append(
                PermissionFactory.get_or_create(
                    action=ActionFactory.get_or_create(action),
                    effect=(
                        Effect.ALLOW if statement["Effect"] == "Allow" else Effect.DENY
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

    print(graph.summary())
    save_graph_pdf(graph, output_path / "iam_graph.pdf")
