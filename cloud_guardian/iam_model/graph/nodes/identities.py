import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Union
from loguru import logger
from cloud_guardian.utils.shared import identities_path


@dataclass
class Entity:
    """Defines a base IAM entity"""

    id: str
    name: str
    includes: List[str] = field(default_factory=list)


def create_entity_class(class_name: str, class_attrs: Dict[str, any]) -> Type[Entity]:
    return type(class_name, (Entity,), class_attrs)


@dataclass
class Resource:
    """Defines a base Resource entity"""

    id: str
    name: str
    type: Optional[str] = None


def create_resource_class(
    class_name: str, class_attrs: Dict[str, any]
) -> Type[Resource]:
    return type(class_name, (Resource,), class_attrs)


def load_classes_from_json(json_file_path: str) -> Dict[str, Type[Entity]]:
    with open(json_file_path, "r") as file:
        data = json.load(file)

        entity_constructors = {}
        resource_constructors = {}

        for class_name, class_attrs in data["identities"].items():
            if class_attrs["category"] == "entity":
                entity_constructors[class_name] = create_entity_class(
                    class_name, class_attrs
                )
            elif class_attrs["category"] == "resource":
                resource_constructors[class_name] = create_resource_class(
                    class_name, class_attrs
                )
            else:
                logger.warning(f"unknown class category: {class_attrs['category']}")

        return entity_constructors, resource_constructors


entity_constructors, resource_constructors = load_classes_from_json(identities_path)


def create_identity(
    identity_type: str,
    identity_id: str,
    name: Optional[str] = None,
    type_str: Optional[str] = None,
) -> Union[Entity, Resource]:
    """
    Create either an entity or a resource based on the given type with the provided ID.
    """
    if identity_type in entity_constructors:
        constructor = entity_constructors[identity_type]
        return constructor(id=identity_id, name=name if name else type_str)
    elif identity_type in resource_constructors:
        constructor = resource_constructors[identity_type]
        return constructor(id=identity_id, name=name if name else type_str)
    else:
        logger.warning(f"unknown identity type: {identity_type}")
