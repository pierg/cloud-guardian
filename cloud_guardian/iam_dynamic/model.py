from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from cloud_guardian.aws.manager import AWSManager
from cloud_guardian.iam_dynamic.actions.supported import (
    SupportedAction,
    SupportedActionsFactory,
    supported_actions_ids,
)
from cloud_guardian.iam_static.graph.graph import IAMGraph
from cloud_guardian.iam_static.graph.identities.group import Group
from cloud_guardian.iam_static.graph.identities.role import Role
from cloud_guardian.iam_static.graph.identities.services import SupportedService
from cloud_guardian.iam_static.graph.identities.user import User
from cloud_guardian.iam_static.model import IAMManager
from cloud_guardian import logger

class Parameters(dict):
    """Extends dictionary to provide additional functionality or validation if necessary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def from_dict(cls, data: dict):
        """Factory method to create Parameters from a dictionary."""
        return cls(data)

    def to_dict(self):
        """Convert Parameters back to a dictionary, can be used for serialization."""
        return dict(self)


@dataclass
class Transition:
    entity: Union[User, Role, Group, SupportedService]
    action: SupportedAction
    parameters: Parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity.name,
            "action": self.action.aws_action_id,
            "parameters": self.parameters.to_dict(),
        }

    @classmethod
    def from_dict(cls, graph: IAMGraph, data: Dict[str, Any]) -> "Transition":
        entity = graph.get_entity_by_id(data["entity"])
        action = SupportedActionsFactory.get_action_by_id(data["action"])
        parameters = Parameters.from_dict(data["parameters"])
        return cls(entity=entity, action=action, parameters=parameters)

    def to_commands(self) -> List[str]:
        return self.action.commands(**self.parameters.details)


@dataclass
class IAMGraphMDP:
    iam_manager: IAMManager
    aws_manager: AWSManager
    trace: List[Transition] = field(default_factory=list)

    def step(
        self,
        entity: Union[User, Role, Group, SupportedService],
        action_id: str,
        parameters: Parameters,
    ):
        # Apply action on the graph
        logger.info(
            f"Applying action {action_id} to entity {entity} with parameters {parameters}"
        )

        # Use the factory to create the appropriate action
        action = SupportedActionsFactory.get_action_by_id(action_id)

        action.apply(self.aws_manager, self.iam_manager, **parameters)

        # Record the transition
        transition = Transition(entity=entity, action=action, parameters=parameters)

        self.trace.append(transition)

    def to_dict(self) -> Dict[str, Any]:
        return {"transitions": [transition.to_dict() for transition in self.trace]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], initial_graph: IAMGraph) -> "IAMGraphMDP":
        mdp = cls(graph=initial_graph)
        mdp.execute_trace(data)

    def step_from_dict(self, transition_data: Dict[str, Any]):
        action_id = transition_data["action"]
        parameters = Parameters.from_dict(transition_data["parameters"])
        # entity = self.iam_manager.graph.get_entity_by_name(transition_data["entity"])
        # TODO: remove after TODOs are done
        entity = "arn:aws:iam::123456789012:user/Eve"
        self.step(entity, action_id, parameters)

    def execute_trace(self, trace: dict):
        for transition_data in trace.get("transitions", []):
            self.step_from_dict(transition_data)

    def to_commands(self) -> List[str]:
        commands = []
        for transition in self.trace:
            commands.extend(transition.to_commands())
        return commands

    def get_actions(self, node_id: str) -> List[SupportedAction]:
        """
        Returns a list of all actions that can be applied to the current graph state.
        """

        relationships = self.iam_manager.graph.get_relationships_from_node(
            node_id, filter_types=["permission"]
        )
        supported_actions = []
        for relationship in relationships:
            supported_actions.extend(
                relationship.permission.action.find_matching_actions(
                    supported_actions_ids
                )
            )
        if self.iam_manager.graph.get_relationships_from_node(
            node_id, filter_types=["can_assume_role"]
        ):
            supported_actions.extend("AssumeRole")

        return supported_actions
