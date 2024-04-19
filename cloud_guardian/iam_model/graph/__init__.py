from cloud_guardian.iam_model.graph.permissions import all_action_types
from cloud_guardian.iam_model.graph.identities import (
    entity_constructors,
    resource_constructors,
)
from loguru import logger


# constraints per tuple
# (source, target) -> [] constraints
class AllConstraints:
    def __init__(self):
        # map: source -> map: target -> [constraints]
        self.map = {}

        # tracks constraints per target when source is unknown
        self.any_source = {}

        # tracks constraints per source when target is unknown
        self.any_target = {}

    def add(self, source_node, target_node, constraint):
        source_node = source_node.lower()
        target_node = target_node.lower()

        self.map.setdefault(source_node, {}).setdefault(target_node, []).append(
            constraint
        )
        if constraint not in self.any_source.get(target_node, []):
            self.any_source.setdefault(target_node, []).append(constraint)

        if constraint not in self.any_target.get(source_node, []):
            self.any_target.setdefault(source_node, []).append(constraint)

    def get(self, source, target):
        source_node = type(source).__name__.lower()
        target_node = type(target).__name__.lower()

        if source_node in self.map and target_node in self.map[source_node]:
            return self.map[source_node][target_node]
        else:
            return None

    def get_any_source(self, target):
        return self.any_source[target]

    def get_any_target(self, target):
        return self.any_target[source]

    def print_all_constraints(self):
        print("\n= All constraints =")
        for source, inner_map in self.map.items():
            for target, constraints in inner_map.items():
                for constraint in constraints:
                    print(f"({source} -[{constraint.__name__}]-> {target}")

        print("\n= Constraints: any source =")
        for target, constraints in self.any_source.items():
            for constraint in constraints:
                print(f"* -[{constraint.__name__}]-> {target}")

        print("\n= Constraints: any target =")
        for source, constraints in self.any_target.items():
            for constraint in constraints:
                print(f"{source} -[{constraint.__name__}]-> *")


# map: subsuming categories -> items belonging to them
class AllInclusions:
    def __init__(self):
        self.inclusions = {}

        for constructors in [entity_constructors, resource_constructors]:
            for constructor_name, constructor in constructors.items():
                if constructor.includes:
                    inclusion = [
                        s.lower() for s in constructor.includes if isinstance(s, str)
                    ]
                    category = constructor.category.lower()
                    if category not in ["entity", "resource"]:
                        logger.warning(f"Unknown category: {category}")
                        continue
                    self.inclusions.setdefault(category, {})[
                        constructor_name.lower()
                    ] = inclusion

    def includes(self, category, item):
        item = item.lower()
        if category not in self.inclusions or item not in self.inclusions[category]:
            return []
        else:
            return self.inclusions[category][item]


all_constraints = AllConstraints()
all_inclusions = AllInclusions()

# based on the dictionaries above build datastructures to store all constraints of "allowed_between"
for action in all_action_types:
    for allowed_transition in action.allowed_between:
        sources, targets = allowed_transition["source"], allowed_transition["target"]

        for source in sources:
            for target in targets:
                all_constraints.add(source, target, action)

                # process hierarchical inclusions
                # ... per source (entities)
                for sub_source in all_inclusions.includes("entity", source):
                    all_constraints.add(sub_source, target, action)

                # ... per target (resources)
                for sub_target in all_inclusions.includes("resource", target):
                    all_constraints.add(source, sub_target, action)

# for debugging purposes:
# all_constraints.print_all_constraints()
