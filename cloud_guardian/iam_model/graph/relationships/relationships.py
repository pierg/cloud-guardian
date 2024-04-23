from dataclasses import dataclass
from typing import Union

# Import classes from the cloud_guardian package; assuming they're defined correctly elsewhere
from cloud_guardian.iam_model.graph.identities.group import Group
from cloud_guardian.iam_model.graph.identities.resources import Resource
from cloud_guardian.iam_model.graph.identities.role import Role
from cloud_guardian.iam_model.graph.identities.services import SupportedService
from cloud_guardian.iam_model.graph.identities.user import User
from cloud_guardian.iam_model.graph.permission.actions import AssumeRole, SupportedAction
from cloud_guardian.iam_model.graph.permission.permission import Permission


@dataclass
class Relationship:
    """Base class to represent relationships between two nodes in an IAM graph."""

    source: Union[User, Group, Role, SupportedService]
    target: Union[User, Group, Role, SupportedService, Resource]

    def supports_action(self, action: SupportedAction) -> bool:
        """Check if the relationship supports a given action."""
        # Default implementation, to be overridden by subclasses
        return False

@dataclass
class IsPartOf(Relationship):
    """Represents a 'is part of' relationship where a user or role is part of a group."""

    def supports_action(self, action: SupportedAction) -> bool:
        # Here we specify which actions are supported when a user or role is part of a group
        return isinstance(action, (SupportedAction.AssumeRole, SupportedAction.ReadyOnlyAccess))

@dataclass
class CanAssumeRole(Relationship):
    """Represents a 'can assume role' relationship where a user, group, role, or service can assume another role."""

    def supports_action(self, action: SupportedAction) -> bool:
        return isinstance(action, AssumeRole)

@dataclass
class HasPermissionToResource(Relationship):
    """Represents a 'has permission to' relationship between a user, role, service, or group and a specific resource."""

    permission: Permission

    def supports_action(self, action: SupportedAction) -> bool:
        return action.id == self.permission.action.id and self.permission.effect == "ALLOW"

@dataclass
class HasPermission(Relationship):
    """Represents a 'has permission' relationship on a single node e.g., permissions like CreateRole, DeleteRole."""

    permission: Permission

    def __post_init__(self):
        self.target = self.source

    def supports_action(self, action: SupportedAction) -> bool:
        return action.id == self.permission.action.id and self.permission.effect == "ALLOW"
