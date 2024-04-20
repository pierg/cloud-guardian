from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any
from cloud_guardian.iam_model.graph.permission.permission import Permission
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities.models import Entity, Resource


class Action(ABC):
    """Abstract base class for all actions that can be applied to an IAM graph."""

    @abstractmethod
    def apply(self, graph: IAMGraph):
        """Apply the action to the IAM graph."""
        pass


@dataclass
class CreateNodeAction(Action):
    node_id: str
    node_category: str  # entity or resource
    node_class: str  # user, group, role, policy, etc.
    properties: Dict[str, Any]

    def apply(self, graph: IAMGraph):
        if self.node_category == "entity":
            node = Entity.create_from_dict(self.node_class, self.properties)
        elif self.node_category == "resource":
            node = Resource.create_from_dict(self.node_class, self.properties)
        graph.add_node(node)


@dataclass
class DeleteNodeAction(Action):
    node_id: str

    def apply(self, graph: IAMGraph):
        graph.remove_node(self.node_id)
        # Remove all edges connected to this node
        graph.edges.pop(self.node_id, None)
        for edge_dict in graph.edges.values():
            edge_dict.pop(self.node_id, None)


@dataclass
class AddPermissionAction(Action):
    source: str
    target: str
    permission: Permission

    def apply(self, graph: IAMGraph):
        graph.edges.setdefault(self.source, {}).setdefault(self.target, self.permission)


@dataclass
class RemovePermissionAction(Action):
    source: str
    target: str

    def apply(self, graph: IAMGraph):
        if self.target in graph.edges.get(self.source, {}):
            del graph.edges[self.source][self.target]


@dataclass
class ModifyAttributeAction(Action):
    node_id: str
    key: str
    value: Any
    operation: str  # 'add' or 'remove'

    def apply(self, graph: IAMGraph):
        if self.operation == "add":
            graph.nodes[self.node_id].attributes[self.key] = self.value
        elif self.operation == "remove":
            graph.nodes[self.node_id].attributes.pop(self.key, None)
