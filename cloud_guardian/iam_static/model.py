import re

from cloud_guardian import logger
from cloud_guardian.aws.helpers.generic import get_identity_or_resource_from_arn
from cloud_guardian.aws.helpers.s3.bucket_operations import list_buckets
from cloud_guardian.aws.helpers.s3.bucket_policy import get_bucket_policy
from cloud_guardian.aws.manager import AWSManager
from cloud_guardian.iam_static.graph.graph import IAMGraph
from cloud_guardian.iam_static.graph.identities.group import Group
from cloud_guardian.iam_static.graph.identities.resources import (
    Resource,
)
from cloud_guardian.iam_static.graph.identities.role import Role
from cloud_guardian.iam_static.graph.identities.user import User
from cloud_guardian.iam_static.graph.permission.actions import ActionsFactory
from cloud_guardian.iam_static.graph.permission.effects import Effect
from cloud_guardian.iam_static.graph.permission.permission import PermissionFactory
from cloud_guardian.utils.strings import pretty_print


class IAMManager:
    # It only *pulls / reads* data from AWS and updates the graph
    # It does NOT *push / write* data to AWS

    def __init__(self, aws_manager: AWSManager):
        self.iam = aws_manager.iam
        self.s3 = aws_manager.s3
        self.graph = IAMGraph()

    def update_graph(self):
        # TODO: use the helper functions in
        # cloud_guardian.aws.helpers.iam and cloud_guardian.aws.helpers.s3 (or add new ones if needed)
        # with the rerefence self.iam and self.s3 to
        # pull the data needed to populate self.graph data structures without adding new ones (no Policy etc..)
        # then delete analyzer.py, analyzer_old etc..
        # Use the methods below when possible, add new ones if needed

        # get all policy statements
        statements = []
        for bucket in list_buckets(self.s3):
            # pretty_print(bucket)
            # pretty_print(get_bucket_policy(self.s3, bucket["name"]))
            policy_document = get_bucket_policy(self.s3, bucket["name"])[
                "PolicyDocument"
            ]
            for statement in policy_document["Statement"]:
                statements.append(statement)

        # TODO: process the statements one by one to update the graph
        # principal -(permission: effect+action)-> resources
        for statement in statements:
            source_arn = statement["Principal"]["ID"]
            self.graph.get_relationships_from_node(source_arn)
            pretty_print(statement)
            print("FIXME")

            for resource_arn in statement["Resource"]:
                # FIXME: invalid custom ARN:
                # "arnparse.arnparse.MalformedArnError: arn_str: custom_id___custom__:group/BasicUsers"
                #
                source_dict = get_identity_or_resource_from_arn(
                    source_arn, self.iam, self.s3
                )

                # FIXME: transform the `ResponseMetadata` object in a Resource object (no apparent link)
                # example of data returned by `get_identity_or_resource_from_arn`:
                # {'ResponseMetadata': {'RequestId': 'Z5E917JYdui8gdH45JeV68dKYBxuuzntxbPYzMmnG5Eky3j11g9W', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'Z5E917JYdui8gdH45JeV68dKYBxuuzntxbPYzMmnG5Eky3j11g9W'}, 'RetryAttempts': 0}, 'Owner': {'DisplayName': 'webfile', 'ID': '75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a'}, 'Grants': [{'Grantee': {'ID': '75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a', 'Type': 'CanonicalUser'}, 'Permission': 'FULL_CONTROL'}]}
                #
                # As a consequence, the target object cannot be retrieved from the Resource factory
                target_dict = get_identity_or_resource_from_arn(
                    resource_arn, self.iam, self.s3
                )

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

                    # TODO: process (source, target, permission)
                    # check if these characteristics are already in an existing edge
                    # (from `existing_relationships`: check source, target, and permission ID)
                    # if so: remove/update existing relationship
                    # otherwise: add relationship

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

    def update_permissions_to_node(self, policy_document: dict, arn: str):
        # TODO
        # policy_document is the policy document in json format (dict) e.g. {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::examplebucket/*"}]}
        # Create/Update Permission objects and attach to the nodes in the graph, etc..

        # FIXME: the edges retrieved from self.graph.graph.edges() do not contain enough information
        # to update the edges, and consequently the policies attached to an entity (edge: HadPermission)
        pass

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
