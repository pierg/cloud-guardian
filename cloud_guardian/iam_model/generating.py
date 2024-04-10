import ipaddress
import random

from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.identities import create_entity
from cloud_guardian.iam_model.graph.permission import Condition, Effect, Permission
from cloud_guardian.iam_model.validating import Validate


def _generate_random_condition() -> Condition:
    condition_types = ["equals", "in_range", "time_between"]
    value_types = ["integer", "ip", "time"]

    # Randomly select condition and value types
    condition_type = random.choice(condition_types)
    value_type = random.choice(value_types)

    if condition_type == "equals":
        if value_type == "integer":
            value = random.randint(1, 100)
        elif value_type == "ip":
            value = str(ipaddress.IPv4Address(random.randint(0, 2**32 - 1)))
        elif value_type == "time":
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            value = f"{hour:02d}:{minute:02d}"
        condition_str = f"example_key=={value}"

    elif condition_type == "in_range":
        start = random.randint(1, 50)
        end = random.randint(51, 100)
        value = f"{start}-{end}"
        condition_str = f"range_key=={value}"

    elif condition_type == "time_between":
        start_hour = random.randint(0, 22)
        end_hour = start_hour + 1
        start_minute = random.randint(0, 59)
        end_minute = random.randint(0, 59)
        value = f"{start_hour:02d}:{start_minute:02d}-{end_hour:02d}:{end_minute:02d}"
        condition_str = f"time_key=={value}"

    return Condition.from_string(condition_str)


def generate_random_IAMGraph(
    num_entities: int, num_resources: int, num_permissions: int
) -> IAMGraph:
    graph = IAMGraph()

    # Generate random nodes
    for i in range(num_entities):
        entity_str = random.choice(Validate.get_valid_entities_str())

        entity_id = f"{entity_str}_{i}"  # Generating a unique ID
        entity = create_entity(entity_str, entity_id)
        graph.add_node(entity)

    # Generate random nodes
    for i in range(num_entities, num_resources):
        resource_str = random.choice(Validate.get_valid_resources_str())

        resource_id = f"{resource_str}_{i}"  # Generating a unique ID
        resource = create_entity(resource_str, resource_id)
        graph.add_node(resource)

    # Generate random edges with permissions
    nodes = list(graph.graph.nodes())
    for _ in range(num_permissions):
        source_id, target_id = random.sample(nodes, 2)
        source_node = graph.graph.nodes[source_id]["instance"]
        target_node = graph.graph.nodes[target_id]["instance"]
        possible_actions = Validate.get_valid_actions_between_nodes(
            source_node, target_node
        )
        print(possible_actions)
        if possible_actions:
            action = random.choice(list(possible_actions))
            # Add randomly with probability of 0.2 a ~ in front of action_str
            if random.random() < 0.2:
                prefex = "~"
                Effect.DENY
            else:
                prefex = ""
                Effect.ALLOW

            # Generate a random condition string for the permission wit probability of 0.1
            condition = _generate_random_condition() if random.random() < 0.1 else ""
            permission = Permission(
                id=prefex + action.name,
                effect=Effect.ALLOW,
                action=action,
                conditions=[condition],
            )

            print(
                f"Adding edge from {source_node.id} to {target_node.id} with permission {permission}"
            )
            graph.add_edge(source_node, target_node, permission)

    return graph
