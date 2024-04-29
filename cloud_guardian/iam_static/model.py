import re

from cloud_guardian import logger
from cloud_guardian.aws.helpers.generic import get_identity_or_resource_from_arn
from cloud_guardian.aws.helpers.s3.bucket_operations import list_buckets
from cloud_guardian.aws.helpers.s3.bucket_policy import get_bucket_policy
from cloud_guardian.aws.manager import AWSManager
from cloud_guardian.iam_static.graph.graph import IAMGraph
from cloud_guardian.iam_static.graph.identities.group import Group, GroupFactory
from cloud_guardian.iam_static.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_static.graph.identities.role import Role, RoleFactory
from cloud_guardian.iam_static.graph.identities.user import User, UserFactory
from cloud_guardian.iam_static.graph.permission.actions import ActionsFactory
from cloud_guardian.iam_static.graph.permission.effects import Effect
from cloud_guardian.iam_static.graph.permission.permission import PermissionFactory
from cloud_guardian.iam_static.graph.relationships.relationships import (
    HasPermissionToResource,
)


class IAMManager:
    # It only *pulls / reads* data from AWS and updates the graph
    # It does NOT *push / write* data to AWS

    def __init__(self, aws_manager: AWSManager):
        self.iam = aws_manager.iam
        self.s3 = aws_manager.s3
        self.graph = IAMGraph()

    def update_graph(self):
        for bucket in list_buckets(self.s3):
            policy_document = get_bucket_policy(self.s3, bucket["name"])[
                "PolicyDocument"
            ]
            self.update_permissions_to_node(policy_document)

    def update_node(self, arn: str):
        # get updated info from the IAM client
        entity = get_identity_or_resource_from_arn(arn, self.iam, self.s3)
        if not entity:
            logger.error(f"Unable to update node: {arn} does not exist")
            return

        # extract entity type from ARN
        entity_type = re.search(r"(?<=:)([^/:]+)(?=\/)", arn).group(1)

        # check if the node already exists in the graph
        for node_id, node_attrs in self.graph.graph.nodes(data=True):
            if node_attrs.get("Arn") == arn:
                # Node already exists: update it
                logger.info(f"Updating node {node_id}")
                self.graph.graph.nodes[node_id].update(entity)
                return

        # if the node does not exist: create it
        logger.info(f"Creating node {entity}")
        if entity_type == "user":
            self._add_user(entity["UserName"], entity["Arn"], entity["CreateDate"])
        elif entity_type == "role":
            self._add_role(entity["RoleName"], entity["Arn"], entity["CreateDate"])
        elif entity_type == "group":
            self._add_group(entity["GroupName"], entity["Arn"], entity["CreateDate"])

    def update_permissions_to_node(self, policy_document: dict):
        for statement in policy_document["Statement"]:
            for resource_arn in statement["Resource"]:
                # source
                source_dict = get_identity_or_resource_from_arn(
                    statement["Principal"]["ID"], self.iam, self.s3
                )

                if "GroupName" in source_dict:
                    source = GroupFactory.get_or_create(
                        name=source_dict["GroupName"],
                        arn=source_dict["Arn"],
                        create_date=source_dict["CreateDate"],
                    )
                elif "RoleName" in source_dict:
                    source = RoleFactory.get_or_create(
                        name=source_dict["RoleName"],
                        arn=source_dict["Arn"],
                        create_date=source_dict["CreateDate"],
                    )
                elif "UserName" in source_dict:
                    source = UserFactory.get_or_create(
                        name=source_dict["UserName"],
                        arn=source_dict["Arn"],
                        create_date=source_dict["CreateDate"],
                    )
                else:
                    logger.error(f"Unknown source: {source_dict}")

                if source not in self.graph.get_nodes():
                    self.graph.graph.add_node(source)

                # target
                target_dict = get_identity_or_resource_from_arn(
                    resource_arn, self.iam, self.s3
                )

                target = ResourceFactory.get_or_create(
                    name=target_dict["Name"],
                    arn=target_dict["ARN"],
                    service=target_dict["Service"],
                    resource_type=None,
                )

                if target not in self.graph.get_nodes():
                    self.graph.graph.add_node(target)

                # clear the relationships between the source and the target
                self.graph.graph.remove_edge(source, target)

                for action in statement["Action"]:
                    permission = PermissionFactory.get_or_create(
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

                    # FIXME: indicates that the node is not in the graph while it necessarily
                    # has been added (lines 97 and 112 above)
                    self.graph.add_relationship(
                        HasPermissionToResource(
                            source=source,
                            target=target,
                            permission=permission,
                        )
                    )

    def _add_user(self, name: str, arn: str, create_date: str):
        user = User(
            name=name,
            arn=arn,
            create_date=create_date,
        )

        if user in self.graph.graph.nodes():
            logger.warning(f"Cannot add user {user.id} (already exists)")
            return

        self.graph.graph.add_node(user)

    def _add_role(self, name: str, arn: str, create_date: str):
        role = Role(
            name=name,
            arn=arn,
            create_date=create_date,
        )

        if role in self.graph.graph.nodes():
            logger.warning(f"Cannot add role {role.id} (already exists)")
            return

        self.graph.graph.add_node(role)

    def _add_group(self, name: str, arn: str, create_date: str):
        group = Group(
            name=name,
            arn=arn,
            create_date=create_date,
        )

        if group in self.graph.graph.nodes():
            logger.warning(f"Cannot add group {group.id} (already exists)")
            return

        self.graph.graph.add_node(group)

    def _add_resource(self, name: str, arn: str, service: str, resource_type: str):
        resource = Resource(
            name=name,
            arn=arn,
            service=service,
            resource_type=resource_type,
        )

        if resource in self.graph.graph.nodes():
            logger.warning(f"Cannot add resource {resource.id} (already exists)")
            return

        self.graph.graph.add_node(resource)

    def _remove_user():
        # TODO: check edges / permissions attached and other ndoes affected by it
        pass

    def _remove_role():
        # TODO: check edges / permissions attached and other ndoes affected by it
        pass

    def _remove_group():
        # TODO: check edges / permissions attached and other ndoes affected by it
        pass

    def _remove_resource():
        # TODO: check edges / permissions attached and other ndoes affected by it
        pass
