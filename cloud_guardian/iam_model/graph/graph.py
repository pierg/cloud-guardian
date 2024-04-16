from dataclasses import dataclass, field
from typing import Dict, Set, Union

import networkx as nx
from cloud_guardian.iam_model.graph.edges.action import IAMAction
from cloud_guardian.iam_model.graph.edges.permission import Permission
from cloud_guardian.iam_model.graph.nodes import (
    entity_constructors,
    resource_constructors,
)
from cloud_guardian.iam_model.graph.nodes.models import (
    Entity,
    Resource,
)
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

    def add_edge(
        self,
        source_node: Union[Entity, Resource],
        target_node: Union[Entity, Resource],
        permission: Permission,
    ):
        logger.info(
            f"Adding edge from {source_node.id} to {target_node.id} with permission {permission.id}"
        )
        # Validation
        # Retrieve the IAMAction instance corresponding to the permission's action
        action = permission.action
        valid = False
        
        # TODO: Fix, as now classes are loaded dynamically, they are not hierarchically defined, e.g. Entity -> User, Group, Role
        # TODO: change the way validation among allowed_between is done, as now it is not working

        # # Retrieve all class constructors for entities and resources
        # all_constructors = {**entity_constructors, **resource_constructors}

        # for source_types, target_types in action.allowed_between:
        #     # Check if source_node is an instance of any of the allowed source types
        #     if any(
        #         isinstance(source_node, all_constructors.get(src_type, type(None)))
        #         for src_type in source_types
        #     ):
        #         # Check if target_node is an instance of any of the allowed target types
        #         if any(
        #             isinstance(target_node, all_constructors.get(tgt_type, type(None)))
        #             for tgt_type in target_types
        #         ):
        #             valid = True
        #             break

        # if not valid:
        #     logger.error(
        #         f"Action not allowed from {source_node.id} to {target_node.id} with action {action.name}"
        #     )
        #     raise ActionNotAllowedException(source_node, target_node, action)

        self.graph.add_edge(source_node.id, target_node.id, permission=permission)
        logger.info(
            f"Edge successfully added from {source_node.id} to {target_node.id} with permission {permission.id}"
        )

    def get_all_allowable_actions(
        self,
        source_node: Union[Entity, Resource],
        target_node: Union[Entity, Resource, None] = None,
    ) -> Set[IAMAction]:
        """Returns a set of IAMAction instances that are allowable from the specified source node to a target node, or to any target node if target_node is None."""
        allowable_actions = set()

        # Log the operation
        if target_node:
            logger.info(
                f"Getting allowable actions from {source_node.id} to {target_node.id}"
            )
        else:
            logger.info(
                f"Getting all allowable actions from {source_node.id} to any target"
            )

        # Retrieve all class constructors for entities and resources
        all_constructors = {**entity_constructors, **resource_constructors}

        allowable_actions = []

        # Iterate through all possible actions to see which are allowable based on the 'allowed_between' constraints
        for action in IAMAction:
            # source_types and target_types are list of strings
            for source_types, target_types in action.allowed_between:

                # TODO: Fix, same problem as before
                # source_types_concrete = get_all_concrete_types for all source types
                # ["User", "Group", "Role"] fro ["Entity"]

                # Then check if the source node class name is in source_types_concrete and target node class name is in target_types_concrete etc..

                allowable_actions.append(action)

        if allowable_actions:
            logger.info(
                f"Found allowable actions: {[action.name for action in allowable_actions]}"
            )
        else:
            logger.info("No allowable actions found")

        return allowable_actions

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
