from dataclasses import dataclass, field
from typing import Dict, Set, Union

import networkx as nx
from loguru import logger
from numpy import source

from cloud_guardian.iam_model.graph.identities.user import User


from re import U
from typing import Union
from cloud_guardian.iam_model.graph.identities import user
from cloud_guardian.iam_model.graph.permission.permission import PermissionFactory
from cloud_guardian.iam_model.graph.relationships.relationships import Relationship
from cloud_guardian.utils.shared import aws_example_folder
from cloud_guardian.iam_model.graph.identities.group import Group, GroupFactory
from cloud_guardian.iam_model.graph.identities.user import User, UserFactory
from cloud_guardian.iam_model.graph.identities.role import Role, RoleFactory
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
    ResourceFactory,
)
from cloud_guardian.iam_model.graph.identities.services import (
    SupportedService,
    ServiceFactory,
)

from dataclasses import dataclass, field
from typing import Dict, Set, Union

import networkx as nx
from loguru import logger
from numpy import source

from cloud_guardian.iam_model.graph.identities.user import User
import json


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
