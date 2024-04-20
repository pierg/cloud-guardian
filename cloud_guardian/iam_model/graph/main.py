from re import U
from typing import Union
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities import user
from cloud_guardian.iam_model.graph.permission.permission import PermissionFactory
from cloud_guardian.iam_model.graph.relationships.relationships import IsPartOf
from cloud_guardian.utils.shared import aws_example_folder
from cloud_guardian.iam_model.graph.identities.group import Group, GroupFactory
from cloud_guardian.iam_model.graph.identities.user import User, UserFactory
from cloud_guardian.iam_model.graph.identities.role import Role, RoleFactory
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_model.graph.identities.services import (
    SupportedService,
    ServiceFactory,
)

from dataclasses import dataclass, field
from typing import Dict, Set, Union

import networkx as nx
from loguru import logger
from numpy import source

from cloud_guardian.iam_model.graph.identities.user import User
import json

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
        is_part_of_relationship = IsPartOf(user, group)
        graph.add_relationship(is_part_of_relationship)


# TODO: Parse the rest of the relationships (see relationships.py)

# roles.json contain all you need to make the "CanAssumeRole" relationships

# users.json and groups.jsons contain keys for the policy attached to them, so it means that they have all the permissions related to those policy keys, n.b. identity based polices also contain resources as "arn:aws:s3:::example-bucket/*", so that could match multiple resource in the graph.
# So we can have user -> haspermission (permsision_x) -> resource_1
#                user -> haspermission (permsision_x) -> resource_2 etc..
# Check the google doc for more details

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
