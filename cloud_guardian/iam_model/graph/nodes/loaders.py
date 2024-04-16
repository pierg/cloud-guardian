# nodes/constructor_loader.py
import json
from loguru import logger
from cloud_guardian.utils.shared import identities_path
from .models import Entity, Resource

def load_classes_from_json(json_file_path: str):
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        return {'entities': {}, 'resources': {}}
    except json.JSONDecodeError:
        logger.error("JSON decoding error")
        return {'entities': {}, 'resources': {}}

    entity_constructors = {}
    resource_constructors = {}

    for class_name, class_attrs in data.get("identities", {}).items():
        if class_attrs.get("category") == "entity":
            entity_constructors[class_name] = Entity.create_from_dict(class_name, class_attrs)
        elif class_attrs.get("category") == "resource":
            resource_constructors[class_name] = Resource.create_from_dict(class_name, class_attrs)
    
    return {'entities': entity_constructors, 'resources': resource_constructors}
