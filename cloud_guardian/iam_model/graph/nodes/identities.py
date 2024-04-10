from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Union


@dataclass
class Entity:
    """Defines a base IAM entity. Can be a User, Group, or Role."""

    id: str


@dataclass
class User(Entity):
    """Defines a User entity."""

    name: Optional[str] = None


@dataclass
class Group(Entity):
    """Defines a Group entity. Groups contain users."""

    name: Optional[str] = None
    users: List[User] = field(default_factory=list)

    def add_user(self, user: User):
        """Add a user to the group."""
        self.users.append(user)


@dataclass
class Role(Entity):
    """Defines a Role entity. Roles can be associated to multiple policies (inferred from the graph)."""

    name: Optional[str] = None


@dataclass
class Resource:
    """Defines a base Resource entity. Can be a Datastore or Compute."""

    id: str
    type: Optional[str] = None


@dataclass
class Datastore(Resource):
    """Defines a Datastore resource."""


@dataclass
class Compute(Resource):
    """Defines a Compute resource."""


entity_constructors: Dict[str, Type[Entity]] = {
    "Entity": Entity,
    "User": User,
    "Group": Group,
    "Role": Role,
}

resource_constructors: Dict[str, Type[Resource]] = {
    "Resource": Resource,
    "Datastore": Datastore,
    "Compute": Compute,
}


def create_identity(
    identity_type: str,
    identity_id: str,
    name: Optional[str] = None,
    type_str: Optional[str] = None,
) -> Union[Entity, Resource]:
    """
    Create either an entity or resource based on the given type with the provided ID.
    If 'identity_type' matches an entity, it may also take a 'name'.
    If 'identity_type' matches a resource, it may also take a 'type_str'.
    """
    if identity_type in entity_constructors:
        constructor = entity_constructors[identity_type]
        return constructor(id=identity_id)
    elif identity_type in resource_constructors:
        constructor = resource_constructors[identity_type]
        return constructor(id=identity_id)
    else:
        raise ValueError(f"Unknown identity type: {identity_type}")
