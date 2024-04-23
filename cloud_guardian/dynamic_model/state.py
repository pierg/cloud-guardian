import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple, Union

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.nodes.models import Entity, Resource


@dataclass
class State:
    """Represents a state in the MDP, encapsulating the set of IAM nodes."""

    # state of the graph at time t
    specification: IAMGraph

    # additional attributes for graph nodes
    attributes: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def set_attribute(self, node_id: str, key: str, value: Any):
        if node_id not in self.attributes:
            self.attributes[node_id] = {}
        self.attributes[node_id][key] = value

    def get_attribute(self, node_id: str, key: str) -> Any:
        return self.attributes.get(node_id, {}).get(key)

    def clone(self) -> "State":
        """Create a deep copy of the state for immutable operations."""
        new_state = State(
            nodes=copy.deepcopy(self.nodes), attributes=copy.deepcopy(self.attributes)
        )
        return new_state


@dataclass
class Action:
    # Can be: 
    # create_node, 
    # delete_node, 
    # add_permission (source, target, permission) between two nodes
    # remove_permission (source, target, permission) between two nodes
    # add_attribute: add attribute to a node
    # remove_attribute: add attribute to a node



@dataclass
class Transition:
    """Defines a transition in the MDP from one state to another via an action."""

    source: State
    action: Action
    target: State



@dataclass
class IAMGraphMDP:
    """A Markov Decision Process model for managing an IAMGraph."""

    current_state: State
    trace: List[Transition] = field(default_factory=list)

    def step(
        self,
        source_node: Entity,
        action: Action,
        target_node: Union[Entity, Resource, None] = None,
    ):
        """
        Apply an action to the current state.
        """
        new_state = self.current_state.clone()

        # Check that action is allowed from the source node
        self.specification.validate_action(source_node, target_node, action)

        # TODO from scratch
        if action == "AssumeRole":
            if target_node:
                new_state.set_attribute(source_node.id, action, target_node.id)
        elif action == "CreateRole":
            # TODO
            pass

        transition = Transition(
            source=self.current_state, action=action.action, target=new_state
        )
        self.trace.append(transition)
        self.current_state = new_state

        return new_state
