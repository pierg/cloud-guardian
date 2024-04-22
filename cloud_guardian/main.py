
from cloud_guardian.iam_model.graph.analyzers import connect_graph
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.utils.shared import aws_example_folder
from loguru import logger
from cloud_guardian.utils.loaders import load_iam_json_data
from cloud_guardian.iam_model.graph.initializers import initialize_factories


def main():
    data = load_iam_json_data(aws_example_folder)
    initialize_factories(data)
    graph = IAMGraph()
    connect_graph(graph, data)

if __name__ == "__main__":
    main()
