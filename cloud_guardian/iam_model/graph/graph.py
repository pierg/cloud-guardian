from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

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

    # as there can be multiple permissions between a given pair of entities,
    # a `nx.MultiDiGraph` is required
    graph: nx.MultiDiGraph = field(default_factory=nx.MultiDiGraph)

    def add_node(self, node: Union[User, Group, Role, Resource, SupportedService]):
        """Add a node to the graph, ensuring the node is not None."""
        if node is None:
            logger.error(f"Attempted to add a None node with ID {id}.")
            return
        node_type = node.__class__.__name__.lower()
        if "service" in node_type:
            node_type = "service"
        self.graph.add_node(node.id, instance=node, type=node_type, label=node.name)
        logger.info(f"Adding node {node.id} of type {node_type}")

    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph."""
        source_id = relationship.source.id
        target_id = relationship.target.id
        if source_id not in self.graph or target_id not in self.graph:
            logger.error(
                f"Attempting to add relationship of type {relationship.type} with non-existent node: {source_id} or {target_id}"
            )
            return
        elif relationship.type == "permission":
            label = relationship.permission.action.id
        else:
            label = relationship.type
        self.graph.add_edge(
            source_id,
            target_id,
            relationship=relationship,
            type=relationship.type,
            label=label,
        )
        logger.info(
            f"Adding relationship of type {relationship.type} from {source_id} to {target_id}"
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

    def get_nodes(
        self, filter_types: Optional[List[str]] = None
    ) -> List[Tuple[str, Dict]]:
        """Get nodes from the graph based on optional type filtering."""
        if filter_types is None:
            return list(self.graph.nodes(data=True))
        else:
            return [
                (node, data)
                for node, data in self.graph.nodes(data=True)
                if data.get("type") in filter_types
            ]

    def get_edges(
        self, filter_types: Optional[List[str]] = None
    ) -> List[Tuple[str, str, Dict]]:
        """Get edges from the graph based on optional type filtering."""
        if filter_types is None:
            return list(self.graph.edges(data=True))
        else:
            return [
                (source, target, data)
                for source, target, data in self.graph.edges(data=True)
                if data.get("type") in filter_types
            ]

    def get_connected_nodes(
        self, node_id: str, filter_types: Optional[List[str]] = None
    ) -> List[str]:
        """Get the IDs of nodes directly connected to a given node, with optional type filtering."""
        connected_nodes = set(self.graph.successors(node_id)) | set(
            self.graph.predecessors(node_id)
        )
        if filter_types:
            # Filter nodes by checking the type in node data
            return [
                node_id
                for node_id in connected_nodes
                if self.graph.nodes[node_id].get("type") in filter_types
            ]
        return list(connected_nodes)

    def get_outgoing_edges(
        self, node_id: str, filter_types: Optional[List[str]] = None
    ) -> List[Tuple[str, str, Dict]]:
        """Get the outgoing edges of a given node with optional type filtering."""
        outgoing_edges = self.graph.out_edges(node_id, data=True)
        if filter_types:
            return [
                (node_id, target, data)
                for _, target, data in outgoing_edges
                if data.get("type") in filter_types
            ]
        return [(node_id, target, data) for _, target, data in outgoing_edges]

    def get_incoming_edges(
        self, node_id: str, filter_types: Optional[List[str]] = None
    ) -> List[Tuple[str, str, Dict]]:
        """Get the incoming edges of a given node with optional type filtering."""
        incoming_edges = self.graph.in_edges(node_id, data=True)
        if filter_types:
            return [
                (source, node_id, data)
                for source, _, data in incoming_edges
                if data.get("type") in filter_types
            ]
        return [(source, node_id, data) for source, _, data in incoming_edges]

    def get_entity_by_id(
        self, id: str
    ) -> Union[User, Group, Role, Resource, SupportedService]:
        """Get an entity from the graph by its ID."""
        node_data = self.graph.nodes.get(id)
        if node_data is None:
            return None
        return node_data.get("instance")

    def get_identities(
        self, filter_types: Optional[List[str]] = None
    ) -> List[Union[User, Group, Role, Resource]]:
        """Get identities from the graph based on optional type filtering."""
        nodes = self.get_nodes(filter_types)
        return [data["instance"] for _, data in nodes if "instance" in data]

    def get_relationships(
        self, filter_types: Optional[List[str]] = None
    ) -> List[Relationship]:
        """Get relationships from the graph based on optional type filtering."""
        edges = self.get_edges(filter_types)
        return [data["relationship"] for _, _, data in edges if "relationship" in data]

    def get_relationships_from_node(
        self, node_id: str, filter_types: Optional[List[str]] = None
    ) -> List[Relationship]:
        """Get relationships originating from a given node with optional type filtering."""
        outgoing_edges = self.get_outgoing_edges(node_id, filter_types)
        relationships = [
            data["relationship"]
            for _, _, data in outgoing_edges
            if "relationship" in data
        ]
        return relationships

    def get_relationships_to_node(
        self, node_id: str, filter_types: Optional[List[str]] = None
    ) -> List[Relationship]:
        """Get relationships targeting a given node with optional type filtering."""
        incoming_edges = self.get_incoming_edges(node_id, filter_types)
        relationships = [
            data["relationship"]
            for _, _, data in incoming_edges
            if "relationship" in data
        ]
        return relationships
