from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any
from cloud_guardian.iam_model.graph.graph import IAMGraph


class Action(ABC):
    """Abstract base class for all actions that can be applied to an IAM graph."""

    @abstractmethod
    def apply(self, graph: IAMGraph):
        """Apply the action to the IAM graph."""
        pass


@dataclass
class CreateNodeAction(Action):
    node_id: str
    node_type: type  # Expected to be a subclass of Entity or Resource
    properties: Dict[str, Any]

    def apply(self, graph: IAMGraph):
        node = self.node_type(id=self.node_id, **self.properties)
        graph.nodes[self.node_id] = node


@dataclass
class DeleteNodeAction(Action):
    node_id: str

    def apply(self, graph: IAMGraph):
        graph.nodes.pop(self.node_id, None)
        # Remove all edges connected to this node
        graph.edges.pop(self.node_id, None)
        for edge_dict in graph.edges.values():
            edge_dict.pop(self.node_id, None)


@dataclass
class AddPermissionAction(Action):
    source: str
    target: str
    permission: "Permission"

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
