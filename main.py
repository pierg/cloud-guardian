from math import log
import sys
from pathlib import Path
import types

from cloud_guardian.dynamic_model.actions import get_all_supported_actions
from cloud_guardian.iam_model.graph.analyzers import connect_graph
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.initializers import initialize_factories
from cloud_guardian.iam_model.graph.plotting import save_graph_pdf
from cloud_guardian.utils.loaders import load_iam_json_data
from cloud_guardian.utils.shared import output_path, data_path
from loguru import logger


aws_example_folder = data_path / "aws_example_pe"


def run_analysis(data_folder: Path, output_file: Path):
    """Run the complete IAM analysis pipeline."""
    try:
        data = load_iam_json_data(data_folder)

        initialize_factories(data)

        graph = IAMGraph()
        connect_graph(graph, data)

        print(graph.summary())

        # Get all supported actions for each relationship
        supported_actions_ids = [action.aws_action_id for action in get_all_supported_actions()]
        for relationship in graph.get_relationships(filter_types=["haspermission", "haspermissiontoresource"]):
            supported_actions = relationship.permission.action.find_matching_actions(supported_actions_ids)
            logger.info(f"Supported actions for node {relationship.source.name} having permissions {relationship.permission.action}: {supported_actions}")

        save_graph_pdf(graph, output_file)

    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
        raise



def main():
    output_file = output_path / "iam_graph.pdf"
    run_analysis(aws_example_folder, output_file)


if __name__ == "__main__":
    main()
