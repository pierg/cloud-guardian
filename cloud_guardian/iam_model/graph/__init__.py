from cloud_guardian.iam_model.graph.edges import all_action_types
from cloud_guardian.iam_model.graph.nodes import entity_constructors, resource_constructors, concrete_entities_constructors, concrete_resources_constructors

# TODO: based on the dicitonaries above build datastructures to store all constratins of "allowed_between"
    # old comment:
        # TODO: Fix, as now classes are loaded dynamically, they are not hierarchically defined, e.g. Entity -> User, Group, Role
        # source_types_concrete = get_all_concrete_types for all source types
        # ["User", "Group", "Role"] fro ["Entity"]

        # Then check if the source node class name is in source_types_concrete and target node class name is in target_types_concrete etc..

