from dataclasses import dataclass, field
from typing import Dict, Union

import networkx as nx
from cloud_guardian.iam_model.graph.identities import Entity, Resource
from cloud_guardian.iam_model.graph.permission import Permission
from cloud_guardian.iam_model.validating import Validate


@dataclass
class IAMGraph:
    """Represents an IAM policy as a directed graph where nodes can be either entities or resources, and edges represent permissions."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    type_index: Dict[str, set] = field(
        default_factory=lambda: {"entity": set(), "resource": set()}
    )

    def add_node(self, node: Union[Entity, Resource]):
        """Add a node to the graph."""
        node_type = "entity" if isinstance(node, Entity) else "resource"
        Validate.node(node)
        self.graph.add_node(node.id, instance=node, type=node_type)
        print(f"Adding node {node.id} of type {node_type}")
        self.type_index[node_type].add(node.id)

    def add_edge(
        self,
        source_node: Union[Entity, Resource],
        target_node: Union[Entity, Resource],
        permission: Permission,
    ):
        """Add an edge to the graph with a permission."""
        Validate.edge(source_node, target_node, permission.action)
        print(
            f"Adding edge from {source_node.id} to {target_node.id} with permission {permission}"
        )
        self.graph.add_edge(source_node.id, target_node.id, permission=permission)

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
