# nodes/constructor_loader.py
import json
from typing import Dict, List, Tuple

from loguru import logger

from .actions import IAMActionType


def load_classes_from_json(
    json_file_path: str,
) -> Tuple[Dict[str, Dict[str, IAMActionType]], List[IAMActionType]]:
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
            classes = {}
            plain_actions = []
            for category, actions in data["actions"].items():
                classes[category] = {}
                for action_id, attrs in actions.items():
                    action_type = IAMActionType.create_from_dict(
                        action_id, {"id": action_id, "category": category, **attrs}
                    )
                    classes[category][action_id] = action_type
                    plain_actions.append(action_type)
            return classes, plain_actions
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
    except json.JSONDecodeError:
        logger.error("JSON decoding error")
    return {}, []
