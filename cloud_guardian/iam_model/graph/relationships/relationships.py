from dataclasses import dataclass
from typing import Union

from cloud_guardian.iam_model.graph.identities.group import Group
from cloud_guardian.iam_model.graph.identities.resources import (
    Resource,
)
from cloud_guardian.iam_model.graph.identities.role import Role
from cloud_guardian.iam_model.graph.identities.services import (
    SupportedService,
)
from cloud_guardian.iam_model.graph.identities.user import User
from cloud_guardian.iam_model.graph.permission.permission import (
    Permission,
)


@dataclass
class Relationship:
    """Base class to represent relationships between two nodes in an IAM graph."""

    source: Union[User, Group, Role, SupportedService]
    target: Union[User, Group, Role, SupportedService, Resource]


@dataclass
class IsPartOf(Relationship):
    """Represents a 'is part of' relationship where a user or role is part of a group."""

    source: Union[User, Role]
    target: Group


@dataclass
class CanAssumeRole(Relationship):
    """Represents a 'can assume role' relationship where a user, group, role, or service can assume another role."""

    target: Role


@dataclass
class HasPermissionToResource(Relationship):
    """Represents a 'has permission to' relationship between a user, role, service, or group and a specific resource."""

    target: Resource
    permission: Permission


@dataclass
class HasPermission(Relationship):
    """Represents a 'has permission' relationship on a single node e.g., permissions like CreateRole, DeleteRole."""

    permission: Permission

    def __post_init__(self):
        self.target = self.source
