from cloud_guardian.utils.shared import actions_path

from cloud_guardian.iam_model.graph.edges.loaders import load_classes_from_json

categorty_actions, all_action_types = load_classes_from_json(actions_path)

print(all_action_types)