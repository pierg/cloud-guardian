from cloud_guardian.iam_static.graph.analyzers_to_remove import connect_graph
from cloud_guardian.iam_static.graph.graph import IAMGraph
from cloud_guardian.iam_static.graph.identities.group import GroupFactory
from cloud_guardian.iam_static.graph.identities.role import RoleFactory
from cloud_guardian.iam_static.graph.identities.services import ServiceFactory
from cloud_guardian.iam_static.graph.identities.user import UserFactory
from cloud_guardian.utils.loaders import load_iam_data_into_dictionaries
from zipp import Path


def initialize_factories(groups_data, policies_data, roles_data, users_data):
    # Handle 'users.json'
    users = users_data
    for user_data in users.get("Users", []):
        UserFactory.from_dict(user_data)

    # Handle 'groups.json'
    groups = groups_data
    for group_data in groups.get("Groups", []):
        GroupFactory.from_dict(group_data)

    # Handle 'roles.json'
    roles = roles_data
    for role_data in roles.get("Roles", []):
        RoleFactory.from_dict(role_data)
        # Process AssumeRolePolicyDocument if it exists
        assume_role_policy = role_data.get("AssumeRolePolicyDocument", {})
        for statement in assume_role_policy.get("Statement", []):
            if "Service" in statement.get("Principal", {}):
                service_principal = statement["Principal"]["Service"]
                ServiceFactory.get_or_create(service_principal)

    # Handle 'resources_policies.json'
    # FIXME: `ResourceFactory.from_dict` is not adapted to the new policies.json contents
    # resources = policies_data
    # for resource_data in resources.get("ResourceBasedPolicies", []):
    #     for statement in resource_data.get("PolicyDocument", []).get("Statement", []):
    #         ResourceFactory.from_dict(statement["Resource"])


def create_graph(data_folder: Path) -> IAMGraph:
    print(data_folder)
    groups_data, policies_data, roles_data, users_data = (
        load_iam_data_into_dictionaries(data_folder)
    )

    initialize_factories(groups_data, policies_data, roles_data, users_data)
    graph = IAMGraph()
    connect_graph(graph, groups_data, policies_data, roles_data, users_data)
    return graph
