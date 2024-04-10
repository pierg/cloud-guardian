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


entity_constructors: Dict[str, Union[Type[Entity], Type[Resource]]] = {
    "Entity": Entity,
    "Resource": Resource,
    "User": User,
    "Group": Group,
    "Role": Role,
    "Datastore": Datastore,
    "Compute": Compute,
}


def create_entity(
    entity_type: str, entity_id: str, name: Optional[str] = None
) -> Entity:
    """
    Create an entity of the given type with the provided ID and name.
    This function relies on the entity_constructors registry to find the appropriate constructor.
    """
    if entity_type in entity_constructors:
        return entity_constructors[entity_type](id=entity_id)
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")
