from dataclasses import dataclass, field
from typing import Union

import networkx as nx
from cloud_guardian.iam_model.graph.identities.group import Group
from cloud_guardian.iam_model.graph.identities.resources import Resource
from cloud_guardian.iam_model.graph.identities.role import Role
from cloud_guardian.iam_model.graph.identities.services import SupportedService
from cloud_guardian.iam_model.graph.identities.user import User
from cloud_guardian.iam_model.graph.relationships.relationships import Relationship
from loguru import logger


@dataclass
class IAMGraph:
    """Represents an IAM policy as a directed graph where nodes are identities and edges can represent different types of relationships."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    def add_node(
        self, id: str, node: Union[User, Group, Role, Resource, SupportedService]
    ):
        """Add a node to the graph, ensuring the node is not None."""
        if node is None:
            logger.error(f"Attempted to add a None node with ID {id}.")
            return
        node_type = node.__class__.__name__.lower()
        if "service" in node_type:
            node_type = "service"
        self.graph.add_node(id, instance=node, type=node_type, label=node.name)
        logger.info(f"Adding node {id} of type {node_type}")

    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph."""
        source_id = relationship.source.id
        target_id = relationship.target.id
        edge_type = relationship.__class__.__name__.lower()
        if source_id not in self.graph or target_id not in self.graph:
            logger.error(
                f"Attempting to add relationship of type {edge_type} with non-existent node: {source_id} or {target_id}"
            )
            return
        if edge_type == "ispartof":
            label = "part_of"
        elif edge_type == "canassumerole":
            label = "assume_role"
        else:
            label = relationship.permission.action.id
        self.graph.add_edge(
            source_id, target_id, relationship=relationship, type=edge_type, label=label
        )
        logger.info(
            f"Adding relationship of type {edge_type} from {source_id} to {target_id}"
        )

    def summary(self) -> str:
        """Return a summary of the graph: counts of each type of node and relationship."""
        types = {}
        for _, node_data in self.graph.nodes(data=True):
            node_type = node_data.get("type", "unknown")
            types[node_type] = types.get(node_type, 0) + 1
        relationship_types = {}
        for _, _, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get("type", "unknown")
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        return f"Graph has {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges\nNode types: {types}\nRelationship types: {relationship_types}"

    def get_nodes(self, filter_types: list[str] = None):
        """Get nodes from the graph, handling possible absence of 'type' in node data safely."""
        if filter_types:
            return [
                node
                for node in self.graph.nodes(data=True)
                if node[1].get("type") in filter_types
            ]
        return list(self.graph.nodes(data=True))

    def get_edges(self, filter_types: list[str] = None):
        """Get edges from the graph."""
        if filter_types:
            return [
                edge
                for edge in self.graph.edges(data=True)
                if edge[2].get("type") in filter_types
            ]
        return list(self.graph.edges(data=True))

    def get_relationships(self, filter_types: list[str] = None):
        """Get relationships from the graph."""
        if filter_types:
            return [
                edge[2]["relationship"]
                for edge in self.graph.edges(data=True)
                if edge[2].get("type") in filter_types
            ]
        return [edge[2]["relationship"] for edge in self.graph.edges(data=True)]
