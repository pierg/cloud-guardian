import random
from dataclasses import dataclass, field
import trace
import networkx as nx
from typing import Dict, Set, Union, List, Optional, Any, Tuple

from networkx import nodes

from cloud_guardian.iam_model.graph.edges.action import IAMAction
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.nodes.models import Entity, Resource



@dataclass
class State:
    nodes: Set[Union[Entity, Resource]] = field(default_factory=set)

@dataclass
class Transition:
    source: State
    action: IAMAction
    target: State

@dataclass
class IAMGraphMDP:
    """
    A Markov Decision Process model for interacting with an IAMGraph.
    """
    # Specification defining all possible behaviours
    specification: IAMGraph

    # Implementation, defining chosen behaviour
    trace: list[Transition] = field(default_factory=list)

    def step(self, 
             source_node: Union[Entity, Resource],
             action: IAMAction,
             target_node: Union[Entity, Resource, None] = None) -> Tuple[IAMGraph, float, bool]:
        """
        Apply an action to the current state and return the new state, reward, and whether it's terminal.
        """
        if action.name == 'CreateRole':
            reward = self.iamgraph.add_node(target_node)

        elif action.name == 'CreateKey':
            # TODO..

        elif action.name == 'AssumeRole':
            # TODO..


        
        return self.current_state, reward, terminal

    def add_node(self, node: Union[Entity, Resource]) -> float:
        """
        Adds a node to the graph and returns a reward for this action.

        Args:
            node (Union[Entity, Resource]): The node to add.

        Returns:
            float: The reward for adding the node.
        """
        if not self.current_state.graph.has_node(node.id):
            self.current_state.add_node(node)
            self.rewards['add_node'] = 1.0  # Example reward
            return 1.0
        return 0.0

    def add_edge(self, source: Union[Entity, Resource], target: Union[Entity, Resource], permission: Permission) -> float:
        """
        Adds an edge to the graph if allowed and returns a reward.

        Args:
            source (Union[Entity, Resource]): The source node for the edge.
            target (Union[Entity, Resource]): The target node for the edge.
            permission (Permission): The permission object defining the edge.

        Returns:
            float: The reward for adding the edge.
        """
        if self.current_state.graph.has_node(source.id) and self.current_state.graph.has_node(target.id):
            try:
                self.current_state.add_edge(source, target, permission)
                self.rewards['add_edge'] = 5.0  # Example reward
                return 5.0
            except ActionNotAllowedException:
                return -1.0
        return 0.0

    def get_possible_actions(self, node: Union[Entity, Resource]) -> List[IAMAction]:
        """
        Determine possible actions from the current state for a given node.

        Args:
            node (Union[Entity, Resource]): The node to evaluate for possible actions.

        Returns:
            List[IAMAction]: A list of possible IAMActions.
        """
        # Example method body; replace with actual logic
        return []

# Example usage of IAMGraphMDP would go here...
