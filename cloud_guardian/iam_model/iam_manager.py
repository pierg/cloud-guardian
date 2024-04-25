from cloud_guardian.aws.aws_manager import AWSManager
from cloud_guardian.iam_model.graph.graph import IAMGraph


class IAMManager:
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
        pass
