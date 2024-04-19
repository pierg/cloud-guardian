from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any
from cloud_guardian.iam_model.graph.Attributes.Attribute import Attribute
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities.models import Entity, Resource

class Action(ABC):
    """Abstract base class for all actions that can be applied to an IAM graph."""

    @abstractmethod
    def apply(self, graph: IAMGraph):
        """Apply the action to the IAM graph."""
        pass


@dataclass
class CreateNode(Action):
    node_id: str
    node_category: str # entity or resource
    node_class: str    # user, group, role, policy, etc.
    properties: Dict[str, Any]

    def apply(self, graph: IAMGraph):
        if self.node_category == 'entity':
            node = Entity.create_from_dict(self.node_class, self.properties)
        elif self.node_category == 'resource':
            node = Resource.create_from_dict(self.node_class, self.properties)
        graph.add_node(node)

@dataclass
class DeleteNode(Action):
    node_id: str

    def apply(self, graph: IAMGraph):
        # TODO
        
        


@dataclass
class AddAttribute(Action):
    node_id: str
    Attribute: Attribute

    def apply(self, graph: IAMGraph):
        # TODO:
        pass

@dataclass
class RemoveAttribute(Action):
    node_id: str
    Attribute: Attribute

    def apply(self, graph: IAMGraph):
        # TODO:
        pass


@dataclass
class RemoveAttribute(Action):
    source: str
    target: str

    def apply(self, graph: IAMGraph):
        if self.target in graph.edges.get(self.source, {}):
            del graph.edges[self.source][self.target]

@dataclass
class ModifyAttribute(Action):
    node_id: str
    key: str
    value: Any
    operation: str  # 'add' or 'remove'

    def apply(self, graph: IAMGraph):
        if self.operation == 'add':
            graph.nodes[self.node_id].Attribute[self.key] = self.value
        elif self.operation == 'remove':
            graph.nodes[self.node_id].Attribute.pop(self.key, None)
