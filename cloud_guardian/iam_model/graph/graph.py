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
    """Represents an IAM policy as a directed graph where nodes are identities and edges can represent different types of relationships"""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    def add_node(
        self, id: str, node: Union[User, Group, Role, Resource, SupportedService]
    ):
        """Add a node to the graph."""
        node_type = node.__class__.__name__.lower()
        self.graph.add_node(id, instance=node, type=node_type)
        logger.info(f"Adding node {id} of type {node_type}")

    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph."""
        source_id = relationship.source.id
        target_id = relationship.target.id
        self.graph.add_edge(source_id, target_id, relationship=relationship)
        logger.info(
            f"Adding relationship of type {relationship.__class__.__name__} from {source_id} to {target_id}"
        )
