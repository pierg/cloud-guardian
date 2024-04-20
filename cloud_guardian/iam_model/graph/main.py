from re import U
from cloud_guardian.iam_model.graph.identities import user
from cloud_guardian.iam_model.graph.permission.permission import PermissionFactory
from cloud_guardian.utils.shared import aws_example_folder
from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.resources import ResourceFactory
from cloud_guardian.iam_model.graph.identities.services import ServiceFactory


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


users = UserFactory._instances
groups = GroupFactory._instances
roles = RoleFactory._instances
resources = ResourceFactory._instances

# print(list(users.keys()))
# print(list(groups.keys()))
# print(list(roles.keys()))
# print(list(resources.keys()))

# Parse permissions
# for identity_policy in data["identities_policies.json"]["IdentityBasedPolicies"]:
#     for statement in identity_policy["PolicyDocument"]["Statement"]:
#         PermissionFactory.from_dict(statement)


# Parse permissions
for role in data["roles.json"]["Roles"]:
    for statement in role["AssumeRolePolicyDocument"]["Statement"]:
        PermissionFactory.from_dict(statement)
        

permissions = PermissionFactory._instances
print(list(permissions.keys()))
