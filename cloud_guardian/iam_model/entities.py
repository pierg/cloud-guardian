from dataclasses import dataclass, field
from typing import List, Optional

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