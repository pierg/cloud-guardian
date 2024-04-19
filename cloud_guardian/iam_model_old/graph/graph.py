from dataclasses import dataclass, field
from typing import Dict, Set, Union

import networkx as nx
from cloud_guardian.iam_model.graph import all_constraints
from cloud_guardian.iam_model.graph.permission.actions import IAMActionType
from cloud_guardian.iam_model.graph.permission.permission import Permission
from cloud_guardian.iam_model.graph.exceptions import ActionNotAllowedException
from cloud_guardian.iam_model.graph.identities.models import Entity, Resource
from loguru import logger


@dataclass
class IAMGraph:
    """Represents an IAM policy as a directed graph where nodes can be either entities or resources, and edges represent permissions."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    type_index: Dict[str, set] = field(
        default_factory=lambda: {"entity": set(), "resource": set()}
    )

    def add_node(self, node: Union[Entity, Resource]):
        """Add a node to the graph."""
        node_type = "entity" if isinstance(node, Entity) else "resource"
        self.graph.add_node(node.id, instance=node, type=node_type)
        logger.info(f"Adding node {node.id} of type {node_type}")
        self.type_index[node_type].add(node.id)

    def remove_node(self, node: Union[Entity, Resource]):
        """Remove a node from the graph."""
        self.graph.remove_node(node.id)
        logger.info(f"Removing node {node.id} of type {node.__class__.__name__}")
        self.type_index[node.__class__.__name__.__init__].remove(node.id)

    def add_edge(
        self,
        source_node: Union[Entity, Resource],
        target_node: Union[Entity, Resource],
        permission: Permission,
    ):
        logger.info(
            f"Adding edge from {source_node.id} to {target_node.id} with permission {permission.id}"
        )

        if permission.action in self.get_all_allowable_actions_types(
            source_node, target_node
        ):
            logger.info(
                f"Action {permission.action.id} is allowable from {source_node.id} to {target_node.id}"
            )
        else:
            raise ActionNotAllowedException("Action not allowed between nodes")

        self.graph.add_edge(source_node.id, target_node.id, permission=permission)
        logger.info(
            f"Edge successfully added from {source_node.id} to {target_node.id} with permission {permission.id}"
        )

    def validate_action(
        self,
        source_node: Union[Entity, Resource],
        target_node: Union[Entity, Resource],
        action: str,
    ) -> bool:
        """Check if an action is allowable from the source node to the target node."""
        return action in self.get_all_allowable_actions(source_node, target_node)

    def get_all_allowable_actions(
        self,
        source_node: Union[Entity, Resource, None] = None,
        target_node: Union[Entity, Resource, None] = None,
    ) -> Set[str]:
        """Returns a set of actions that are allowable from the source node to the target node."""
        actions = set()
        action_types = self.get_all_allowable_actions_types(source_node, target_node)
        for action_type in action_types:
            actions.add(action_type.get_all_actions())

        return actions

    def get_all_allowable_actions_types(
        self,
        source_node: Union[Entity, Resource, None] = None,
        target_node: Union[Entity, Resource, None] = None,
    ) -> Set[IAMActionType]:
        """Returns a set of IAMActionTypes that are allowable from the source node to the target node."""
        if source_node is None and target_node is None:
            logger.error("source AND target are not None")

        if source_node is None:
            return all_constraints.get_any_source(target_node)

        elif target_node is None:
            return all_constraints.get_any_target(source_node)

        # fake implementation
        # allowable_actions = all_action_types
        return all_constraints.get(source_node, target_node)

    def get_reachable_nodes_from(
        self, source_node: Union[Entity, Resource]
    ) -> Set[Union[Entity, Resource]]:
        """Returns a set of reachable nodes from the specified source node."""
        return {
            self.graph.nodes[node_id]["instance"]
            for node_id in nx.descendants(self.graph, source_node.id)
        }

    def get_permissions_from_node(
        self, source_node: Union[Entity, Resource]
    ) -> Set[Permission]:
        """Returns a set of permissions that originate from the specified source node."""
        return {
            edge_data["permission"]
            for _, _, edge_data in self.graph.edges(source_node.id, data=True)
        }

    def get_all_type(self, node_type: str) -> Dict[str, Union[Entity, Resource]]:
        """Return a dictionary of all nodes of a specified type ('entity' or 'resource')."""
        return {
            node_id: data["instance"]
            for node_id, data in self.graph.nodes(data=True)
            if data.get("type") == node_type
        }

    def get_nodes_by_type(self, node_type: str) -> set:
        """Return a set of node IDs of a specified type ('entity' or 'resource')."""
        return self.type_index.get(node_type, set())

    def get_node_instances_by_type(self, node_type: str) -> list:
        """Return a list of node instances of a specified type ('entity' or 'resource')."""
        node_ids = self.type_index.get(node_type, set())
        return [self.graph.nodes[node_id]["instance"] for node_id in node_ids]
