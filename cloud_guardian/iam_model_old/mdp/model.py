import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple, Union

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities.models import Entity, Resource


@dataclass
class State:
    """Represents a state in the MDP, encapsulating an IAM graph and additional attributes."""

    graph: IAMGraph
    attributes: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def set_attribute(self, node_id: str, key: str, value: Any):
        self.attributes.setdefault(node_id, {})[key] = value

    def get_attribute(self, node_id: str, key: str) -> Any:
        return self.attributes.get(node_id, {}).get(key)

    def clone(self) -> "State":
        """Create a deep copy of the state for immutable operations."""
        return copy.deepcopy(self)


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

    def apply_action(self, action: Action) -> State:
        """Applies the specified action to the current state and returns the new state."""
        new_state = self.current_state.clone()
        # Apply the action to modify the graph within new_state
        self.execute_action(new_state, action)
        return new_state

    def execute_action(self, state: State, action: Action):
        """Modify the state based on the action."""
        if action.type == "add_permission":
            # Example implementation detail
            src_node = action.details["source"]
            trg_node = action.details["target"]
            permission = action.details["permission"]
            state.graph.edges.setdefault(src_node, {}).setdefault(trg_node, permission)

    def step(self, action: Action):
        """Performs an action transitioning the MDP to the next state."""
        new_state = self.apply_action(action)
        self.trace.append(Transition(self.current_state, action, new_state))
        self.current_state = new_state
