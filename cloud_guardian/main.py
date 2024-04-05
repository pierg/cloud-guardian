from cloud_guardian.iam_model.graph import IAMGraph
from cloud_guardian.utils.data_generator import generate_fake_iam_policies
from cloud_guardian.utils.shared import data_path, output_path

# Generate fake IAM policies
config = {
    "small": {
        "num_nodes": 3,
        "num_resources": 3,
        "num_permissions": 10
    },
    "large": {
        "num_nodes": 30,
        "num_resources": 30,
        "num_permissions": 100
    },
    "larger": {
        "num_nodes": 300,
        "num_resources": 300,
        "num_permissions": 1000
    }
}

def generate_iam_graph(config_selected: str):
    # Select the desired configuration
    selected_config = config[config_selected]

    # Generate fake IAM policies
    data_file = data_path / f"fake_data_{config_selected}.csv"
    generate_fake_iam_policies(selected_config["num_nodes"], selected_config["num_resources"], selected_config["num_permissions"], file_path=data_file)

    # Parse the CSV file and populate IAMGraph
    iam_graph = IAMGraph()
    iam_graph.parse_csv_and_populate(data_file)

    # Save the IAM graph as PDF
    iam_graph.save_graph_pdf(output_path / f"iam_graph_{config_selected}.pdf")


generate_iam_graph("small")
generate_iam_graph("large")
generate_iam_graph("larger")