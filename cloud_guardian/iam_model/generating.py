import random

from cloud_guardian.iam_model.graph.edges.condition import Condition
from cloud_guardian.iam_model.graph.edges.effect import Effect
from cloud_guardian.iam_model.graph.edges.permission import Permission
from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.nodes import concrete_entities_constructors, concrete_resources_constructors

from loguru import logger

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

def generate_random_IAMGraph(num_entities: int, num_resources: int, max_num_permissions: int) -> IAMGraph:
    
    graph = IAMGraph()
    all_nodes = []
    known_nodes = set()
    num_permissions = 0

    def create_node(constructor, node_type, index):
        node_id = f"{constructor.__name__}_{index}"
        node = constructor(node_id)
        all_nodes.append(node)
        logger.info(f"Generated {node_type}: {node_id}")

    # Generate random entities
    for i in range(num_entities):
        entity_class = random.choice(concrete_entities_constructors)
        create_node(entity_class, "Entity", i)

    # Generate random resources
    for i in range(num_resources):
        resource_class = random.choice(concrete_resources_constructors)
        create_node(resource_class, "Resource", i)

    logger.info(f"Generated {num_entities} entities and {num_resources} resources.")
    
    random.shuffle(all_nodes)

    # Randomly choose two nodes and create a permission between them
    while num_permissions < max_num_permissions and len(all_nodes) > 1:
        source_node, target_node = random.sample(all_nodes, 2)
        actions = graph.get_all_allowable_actions(source_node, target_node)
        if actions:
            action = random.choice(list(actions))
            effect = Effect.DENY if random.random() < 0.2 else Effect.ALLOW
            conditions = [_generate_random_condition()] if random.random() < 0.1 else []
            permission = Permission(effect=effect, action=action, conditions=conditions)
            graph.add_edge(source_node, target_node, permission)
            num_permissions += 1
            print(f"Added permission from {source_node} to {target_node}")

            if source_node not in known_nodes:
                graph.add_node(source_node)
                known_nodes.add(source_node)

            if target_node not in known_nodes:
                graph.add_node(target_node)
                known_nodes.add(target_node)

    if num_permissions == 0:
        logger.warning("No edges created, generating graph again")
        return generate_random_IAMGraph(num_entities, num_resources, max_num_permissions)

    return graph
