from cloud_guardian.iam_model.generating import generate_random_IAMGraph
from cloud_guardian.iam_model.plotting import save_graph_pdf
from cloud_guardian.utils.shared import output_path

# Generate fake IAM policies
config = {
    "small": {"num_entities": 3, "num_resources": 3, "num_permissions": 10},
    "large": {"num_entities": 30, "num_resources": 30, "num_permissions": 100},
    "larger": {"num_entities": 300, "num_resources": 300, "num_permissions": 1000},
}


iam_graph = generate_random_IAMGraph(10, 20, 30)
save_graph_pdf(iam_graph, output_path / "random_iam_graph.pdf")
