from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import ResourceFactory
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.services import ServiceFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory


def initialize_factories(data):
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
