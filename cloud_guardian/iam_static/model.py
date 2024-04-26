from cloud_guardian.aws.helpers.generic import get_identity_or_resource_from_arn
from cloud_guardian.aws.manager import AWSManager
from cloud_guardian.iam_static.graph.graph import IAMGraph


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
        pass

    def update_node(self, arn: str):
        # TODO: identity can be a User, Role, Group
        # 1 - get the identity info from aws, 2 - create/update in the graph
        get_identity_or_resource_from_arn(arn, self.iam, self.s3)
        # ...
        pass

    def update_permissions_to_node(self, policy_document: dict, arn: str):
        # TODO
        # policy_document is the policy document in json format (dict) e.g. {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::examplebucket/*"}]}
        # Create/Update Permission objects and attach to the nodes in the graph, etc..
        pass

    def _add_user():
        pass

    def _add_role():
        pass

    def _add_group():
        pass

    def _add_resource():
        pass

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
