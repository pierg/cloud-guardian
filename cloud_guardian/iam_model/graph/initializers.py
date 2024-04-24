from cloud_guardian.iam_model.graph.analyzers import connect_graph
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import ResourceFactory
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.services import ServiceFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.utils.loaders import load_iam_json_data
from zipp import Path


def initialize_factories(data):
    # Handle 'users.json'
    users = data.get("users.json", {})
    for user_data in users.get("Users", []):
        UserFactory.from_dict(user_data)

    # Handle 'groups.json'
    groups = data.get("groups.json", {})
    for group_data in groups.get("Groups", []):
        GroupFactory.from_dict(group_data)

    # Handle 'roles.json'
    roles = data.get("roles.json", {})
    for role_data in roles.get("Roles", []):
        RoleFactory.from_dict(role_data)
        # Process AssumeRolePolicyDocument if it exists
        assume_role_policy = role_data.get("AssumeRolePolicyDocument", {})
        for statement in assume_role_policy.get("Statement", []):
            if "Service" in statement.get("Principal", {}):
                service_principal = statement["Principal"]["Service"]
                ServiceFactory.get_or_create(service_principal)

    # Handle 'resources_policies.json'
    resources = data.get("resources_policies.json", {})
    for resource_data in resources.get("ResourceBasedPolicies", []):
        ResourceFactory.from_dict(resource_data)


def create_graph(data_folder: Path) -> IAMGraph:
    data = load_iam_json_data(data_folder)
    initialize_factories(data)
    graph = IAMGraph()
    connect_graph(graph, data)
    return graph
