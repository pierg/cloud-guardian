from cloud_guardian.iam_model.generating import generate_random_IAMGraph
from cloud_guardian.iam_model.plotting import save_graph_pdf
from cloud_guardian.utils.shared import output_path

# Generate fake IAM policies
config = {
    "small": {"num_entities": 5, "num_resources": 5, "max_num_permissions": 10},
    "large": {"num_entities": 30, "num_resources": 30, "max_num_permissions": 50},
    "larger": {"num_entities": 300, "num_resources": 300, "max_num_permissions": 500},
}


for label, params in config.items():
    iam_graph = generate_random_IAMGraph(**params)
    save_graph_pdf(iam_graph, output_path / f"random_iam_graph_{label}.pdf")
