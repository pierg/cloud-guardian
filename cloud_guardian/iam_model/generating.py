import random

from cloud_guardian.iam_model.graph.edges.condition import Condition
from cloud_guardian.iam_model.graph.edges.effect import Effect
from cloud_guardian.iam_model.graph.edges.permission import Permission
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.nodes.identities import (
    create_identity,
    entity_constructors,
    resource_constructors,
)


def _generate_random_condition() -> Condition:
    # Define a list of mock conditions for demonstration
    conditions = [
        ("ipAddress", "in_range", "192.168.1.0/24", "cidr"),
        ("loginTime", "time_between", "09:00-17:00", "time_range"),
        ("userId", "equals", "42", "integer"),
    ]
    # Randomly select one of the conditions
    condition_key, condition_operator, condition_value, value_type = random.choice(
        conditions
    )
    return Condition(
        condition_key,
        condition_operator,
        Condition.parse_condition_value(condition_value, value_type),
        value_type,
    )


def generate_random_IAMGraph(
    num_entities: int, num_resources: int, num_permissions: int
) -> IAMGraph:
    graph = IAMGraph()

    # Generate random entities
    for i in range(num_entities):
        entity_str = random.choice(list(entity_constructors.keys()))
        entity_id = f"{entity_str}_{i}"
        entity = create_identity(entity_str, entity_id)
        graph.add_node(entity)

    # Generate random resources
    for i in range(num_resources):
        resource_str = random.choice(list(resource_constructors.keys()))
        resource_id = f"{resource_str}_{i}"
        resource = create_identity(resource_str, resource_id, type_str=resource_str)
        graph.add_node(resource)

    print(f"Generated {num_entities} entities and {num_resources} resources.")

    permissions_added = 0
    while permissions_added < num_permissions:
        # Ensures that only pairs with valid actions are considered
        try:
            source_id, target_id = random.sample(list(graph.graph.nodes()), 2)
        except ValueError:
            print("Not enough nodes in the graph to continue adding permissions.")
            break

        source_node = graph.graph.nodes[source_id]["instance"]
        target_node = graph.graph.nodes[target_id]["instance"]

        actions = graph.get_all_allowable_actions(source_node, target_node)
        if not actions:
            continue

        action = random.sample(list(actions), 1)[0]

        effect = Effect.DENY if random.random() < 0.2 else Effect.ALLOW

        conditions = [_generate_random_condition()] if random.random() < 0.1 else []

        permission = Permission(effect=effect, action=action, conditions=conditions)

        graph.add_edge(source_node, target_node, permission)
        permissions_added += 1

    return graph