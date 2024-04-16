import csv
from pathlib import Path
from typing import Union

from cloud_guardian.iam_model.graph.edges.permission import Permission
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.nodes.models import (
    Entity,
    Resource,
    create_entity,
)

# TODO: Refactor and test


def parse_csv_and_populate_graph(iam_graph: IAMGraph, csv_file_path: Path):
    """Populate the graph from a CSV file detailing permissions, entities, and resources."""
    with open(csv_file_path, mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            source_id, permission_str, target_id = (
                row["SourceEntity"],
                row["Permission"],
                row["Target"],
            )
            source_node = _get_or_create_node(iam_graph, source_id)
            target_node = _get_or_create_node(iam_graph, target_id)

            # Check if an edge with the same permission already exists
            existing_edges = iam_graph.graph.get_edge_data(
                source_node.id, target_node.id, default={}
            )
            if not any(
                permission.id == permission_str
                for permission in existing_edges.values()
            ):
                # Add new Permission edge if it doesn't exist
                condition_str = row.get("Condition")
                permission = Permission.from_string(permission_str, condition_str)
                iam_graph.add_edge(source_node, target_node, permission)


def _get_or_create_node(iam_graph: IAMGraph, id: str) -> Union[Entity, Resource]:
    # Check if the node is already in the graph and return its instance
    if id in iam_graph.graph:
        return iam_graph.graph.nodes[id]["instance"]

    # Determine the entity type from the ID prefix
    prefix_to_type = {
        "user": "user",
        "group": "group",
        "role": "role",
        "datastore": "datastore",
        "compute": "compute",
    }
    entity_type = next(
        (
            type_name
            for prefix, type_name in prefix_to_type.items()
            if id.startswith(prefix)
        ),
        None,
    )
    if entity_type is None:
        raise ValueError(f"Unrecognized prefix for ID: {id}")

    # Use create_entity to dynamically determine the type and create a new instance
    new_node = create_entity(entity_type, id)
    iam_graph.add_node(new_node)
    return new_node
