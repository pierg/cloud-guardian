from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.helpers import extract_identifier_from_ARN
from cloud_guardian.iam_model.graph.identities.group import GroupFactory
from cloud_guardian.iam_model.graph.identities.resources import ResourceFactory
from cloud_guardian.iam_model.graph.identities.role import RoleFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.iam_model.graph.relationships.relationships import (
    CanAssumeRole,
    IsPartOf,
    HasPermissionToResource,
    HasPermission
)
from cloud_guardian.iam_model.graph.permission.permission import PermissionFactory



from typing import Dict, List, Set
from cloud_guardian.iam_model.graph.identities.resources import ResourceFactory
from cloud_guardian.iam_model.graph.identities.user import UserFactory
from cloud_guardian.iam_model.graph.permission.permission import Permission, PermissionFactory
from cloud_guardian.iam_model.graph.relationships.relationships import HasPermission, HasPermissionToResource
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
                        user_name=extract_identifier_from_ARN(principal["AWS"]),
                        arn=principal["AWS"],
                        create_date=None,
                    )
                    graph.add_relationship(CanAssumeRole(user, role))


    # TODO:
    # Connect "Has Permission To Resource" and "Has Permission" relationships
   
