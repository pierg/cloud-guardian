import json
from typing import Set, Union

from cloud_guardian.iam_model.graph.identities import (
    Entity,
    Resource,
    entity_constructors,
)
from cloud_guardian.iam_model.graph.permission import IAMAction
from cloud_guardian.utils.shared import constraints_path

# Load constraints from a JSON file.
with open(constraints_path, "r") as file:
    constraints = json.load(file)


class InvalidNodeException(Exception):
    def __init__(self, node_attribute):
        message = f"Invalid node attribute: {node_attribute.__class__.__name__} is neither a valid entity nor a resource."
        super().__init__(message)


class InvalidActionException(Exception):
    def __init__(self, action):
        message = f"Action '{action.name}' is not a valid action or not defined in the constraints."
        super().__init__(message)


class ActionNotAllowedException(Exception):
    def __init__(self, source, target, action):
        message = f"Action '{action.name}' is not allowed from '{source.__class__.__name__}' to '{target.__class__.__name__}'."
        super().__init__(message)


class Validate:
    @staticmethod
    def node(node_attribute):
        """Checks if the node attribute is a valid entity or resource."""
        if (
            node_attribute.__class__.__name__
            not in constraints["entities"] + constraints["resources"]
        ):
            raise InvalidNodeException(node_attribute)

    @staticmethod
    def edge(
        source_node: Union[Entity, Resource],
        target_node: Union[Entity, Resource],
        action: IAMAction,
    ):
        """Validates if an action can be performed from a source node to a target node."""
        action_info = constraints["actions"].get(action.name)
        if not action_info:
            raise InvalidActionException(action)

        for allowed_between in action_info["allowedBetween"]:
            source_classes = [
                entity_constructors[cls] for cls in allowed_between["source"]
            ]
            target_classes = [
                entity_constructors[cls] for cls in allowed_between["target"]
            ]
            if any(isinstance(source_node, cls) for cls in source_classes) and any(
                isinstance(target_node, cls) for cls in target_classes
            ):
                return  # Action is valid

        raise ActionNotAllowedException(source_node, target_node, action)

    @staticmethod
    def is_action_flow_enabler(action: IAMAction) -> bool:
        """Checks if an action is a flow enabler."""
        return constraints[action.name]["flow_enabler"]

    @staticmethod
    def get_valid_entities_str() -> list[str]:
        """Retrieves a list of valid entity types."""
        return constraints["entities"]

    @staticmethod
    def get_valid_resources_str() -> list[str]:
        """Retrieves a list of valid resource types."""
        return constraints["resources"]

    @staticmethod
    def get_valid_conditions_str() -> list[str]:
        """Retrieves a list of valid conditions."""
        return constraints["conditions"]

    @staticmethod
    def get_valid_actions_from_node(node: Union[Entity, Resource]) -> Set[IAMAction]:
        """Retrieves a set of valid actions that can be initiated from the specified node type."""
        valid_actions = set()
        for action_name, action_info in constraints["actions"].items():
            for allowed_between in action_info["allowedBetween"]:
                source_classes = [
                    entity_constructors[cls] for cls in allowed_between["source"]
                ]
                if any(isinstance(node, cls) for cls in source_classes):
                    valid_actions.add(IAMAction.from_string(action_name))
        return valid_actions

    @staticmethod
    def get_valid_actions_between_nodes(
        source_node: Union[Entity, Resource], target_node: Union[Entity, Resource]
    ) -> Set[IAMAction]:
        """Retrieves a set of valid actions that can be performed between the source and target nodes."""
        valid_actions = set()
        for action_name, action_info in constraints["actions"].items():
            for allowed_between in action_info["allowedBetween"]:
                source_classes = [
                    entity_constructors[cls] for cls in allowed_between["source"]
                ]
                target_classes = [
                    entity_constructors[cls] for cls in allowed_between["target"]
                ]
                if any(isinstance(source_node, cls) for cls in source_classes) and any(
                    isinstance(target_node, cls) for cls in target_classes
                ):
                    valid_actions.add(IAMAction.from_string(action_name))
        return valid_actions
