from .loaders import load_classes_from_json
from .utilities import get_concrete_identities
from cloud_guardian.utils.shared import identities_path

constructors = load_classes_from_json(identities_path)

entity_constructors = constructors["entities"]
resource_constructors = constructors["resources"]

concrete_entities_constructors = get_concrete_identities(entity_constructors)
concrete_resources_constructors = get_concrete_identities(resource_constructors)
