from cloud_guardian.iam_model.graph import IAMGraph
from cloud_guardian.utils.data_generator import generate_fake_iam_policies
from cloud_guardian.utils.shared import data_path, output_path

data_file = data_path / "fake_iam_policies_new.csv"

# Generate fake IAM policies
generate_fake_iam_policies(
    num_nodes=3, num_resources=3, num_permissions=10, file_path=data_file
)

# Import them into the IAMGraph
iam_graph = IAMGraph()
iam_graph.parse_csv_and_populate(data_file)

# Print the graph
print(iam_graph.graph.nodes(data=True))


iam_graph.save_graph_pdf(output_path / "iam_graph.pdf")
