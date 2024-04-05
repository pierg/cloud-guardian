import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from cloud_guardian.iam_model.identities import Compute, Datastore, Entity, Group, Resource, Role, User
from iam_model.permission import Condition, IAMAction, Permission


@dataclass
class IAMGraph:
    """Represents an IAM policy as a directed graph where nodes can be either entities or resources, and edges represent permissions."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    type_index: Dict[str, set] = field(
        default_factory=lambda: {"entity": set(), "resource": set()}
    )

    def add_node(self, node: Union[Entity, Resource]):
        node_type = "entity" if isinstance(node, Entity) else "resource"
        self.graph.add_node(node.id, instance=node, type=node_type)
        self.type_index[node_type].add(node.id)

    def get_all_type(self, node_type: str) -> Dict[str, Union[Entity, Resource]]:
        """Return a dictionary of all nodes of a specified type ('entity' or 'resource')."""
        return {
            node_id: data["instance"]
            for node_id, data in self.graph.nodes(data=True)
            if data.get("type") == node_type
        }

    def get_nodes_by_type(self, node_type: str) -> set:
        """Return a set of node IDs of a specified type ('entity' or 'resource')."""
        return self.type_index.get(node_type, set())

    def get_node_instances_by_type(self, node_type: str) -> list:
        """Return a list of node instances of a specified type ('entity' or 'resource')."""
        node_ids = self.type_index.get(node_type, set())
        return [self.graph.nodes[node_id]["instance"] for node_id in node_ids]

    def add_permission(
        self,
        source_id: str,
        target_id: str,
        permission: IAMAction,
        condition: Condition = None,
    ):
        """Add a permission (edge) to the graph."""
        self.graph.add_edge(
            source_id, target_id, permission=permission, condition=condition
        )

    def parse_csv_and_populate(self, csv_file_path: str):
        """Populate the graph from a CSV file detailing permissions, entities, and resources."""
        with open(csv_file_path, mode="r") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                source_id, permission_str, target_id = (
                    row["SourceEntity"],
                    row["Permission"],
                    row["Target"],
                )
                condition = self._parse_condition(row["Condition"])

                # Determine and add the nodes (either as an entity or resource)
                source_node = self._get_or_create_node(source_id)
                target_node = self._get_or_create_node(target_id)
                self.add_node(source_node)
                self.add_node(target_node)

                # Add the permission edge
                permission = IAMAction[permission_str.upper()]
                self.add_permission(source_id, target_id, permission, condition)

    def _parse_condition(self, condition_str: str) -> Union[Condition, None]:
        """Parse a condition string from the CSV into a Condition object, if applicable."""
        if condition_str:
            parts = condition_str.split("==")
            if len(parts) == 2:
                condition_key, condition_value = parts
                if "-" in condition_value:  # Time or IP range
                    return Condition(condition_key, "in_range", condition_value)
                return Condition(condition_key, "equals", condition_value)
        return None

    def _get_or_create_node(self, id: str) -> Union[Entity, Resource]:
        # Check if the node is already in the graph and return its instance
        if id in self.graph:
            return self.graph.nodes[id]["instance"]

        # Determine the type and create a new instance based on the ID prefix
        if id.startswith("User"):
            new_node = User(id=id)
        elif id.startswith("Group"):
            new_node = Group(id=id)
        elif id.startswith("Role"):
            new_node = Role(id=id)
        elif id.startswith("Datastore"):
            new_node = Datastore(id=id)
        elif id.startswith("Compute"):
            new_node = Compute(id=id)
        else:
            raise ValueError(f"Unrecognized prefix for ID: {id}")

        # Dynamically determine node_type for the new instance
        node_type = "entity" if isinstance(new_node, Entity) else "resource"

        # Add the node to the graph with its type and instance as attributes
        self.graph.add_node(id, instance=new_node, type=node_type)

        return new_node

    def save_graph_pdf(self, file_path: Path):
        plt.figure(figsize=(12, 8))

        # Get nodes by type
        entities = self.get_nodes_by_type("entity")
        resources = self.get_nodes_by_type("resource")

        # Calculate positions for a circular layout with entities and resources separated
        total_nodes = len(entities) + len(resources)
        angle_between_nodes = 2 * np.pi / total_nodes

        pos = {}
        # Place entities on one half of the circle
        for i, node_id in enumerate(entities):
            angle = angle_between_nodes * i
            pos[node_id] = (np.cos(angle), np.sin(angle))
        # Place resources on the other half of the circle
        offset = len(entities) * angle_between_nodes
        for i, node_id in enumerate(resources):
            angle = offset + angle_between_nodes * i
            pos[node_id] = (np.cos(angle), np.sin(angle))

        # Node labels based on their ID
        node_labels = {node_id: node_id for node_id in self.graph.nodes()}

        entity_color = "#add8e6"  # Light blue
        resource_color = "#ffb6c1"  # Light red

        # Legend for node types
        entity_legend = plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=entity_color,
            markersize=10,
            label="Entities",
        )
        resource_legend = plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=resource_color,
            markersize=10,
            label="Resources",
        )
        first_legend = plt.legend(
            handles=[entity_legend, resource_legend],
            title="Node Types",
            loc="upper left",
        )
        plt.gca().add_artist(first_legend)  # Add the first legend manually

        # Drawing the nodes with their respective colors
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            nodelist=entities,
            node_color=entity_color,
            label="Entities",
            node_size=300,
        )
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            nodelist=resources,
            node_color=resource_color,
            label="Resources",
            node_size=300,
        )

        # Adjust labels to be above nodes
        label_pos = {
            node: (position[0], position[1] + 0.05) for node, position in pos.items()
        }
        nx.draw_networkx_labels(
            self.graph,
            label_pos,
            labels=node_labels,
            font_size=10,
            verticalalignment="bottom",
        )

        # Draw edges with IAMAction enum values as labels
        edge_labels = {
            (u, v): data["permission"].value[0]
            for u, v, data in self.graph.edges(data=True)
        }

        # Separate edges based on flowEnabler attribute
        flow_enabler_edges = [
            (u, v)
            for u, v, data in self.graph.edges(data=True)
            if data["permission"].flowEnabler
        ]
        other_edges = [
            (u, v)
            for u, v, data in self.graph.edges(data=True)
            if not data["permission"].flowEnabler
        ]

        # Draw flowEnabler edges with red arrows
        nx.draw_networkx_edges(
            self.graph,
            pos,
            edgelist=flow_enabler_edges,
            edge_color="red",
            arrows=True,
            width=1,
            arrowstyle="->",
        )

        # Draw other edges with black arrows (or any color you prefer)
        nx.draw_networkx_edges(
            self.graph, pos, edgelist=other_edges, edge_color="black", arrows=True
        )

        nx.draw_networkx_edge_labels(
            self.graph, pos, edge_labels=edge_labels, label_pos=0.5, font_size=9
        )

        # Legend for edge labels
        # Create handles for the legend, assuming IAMAction is defined with at least READ, WRITE, FULL_CONTROL, EXECUTE, PART_OF
        edge_labels_legend = [
            plt.Line2D(
                [0], [0], color="black", lw=1, label=f"{action.name}: {action.value[0]}"
            )
            for action in IAMAction
        ]
        plt.legend(handles=edge_labels_legend, title="Edge Labels", loc="lower left")

        plt.axis("off")
        plt.tight_layout()
        plt.savefig(file_path, format="pdf")
        plt.close()
