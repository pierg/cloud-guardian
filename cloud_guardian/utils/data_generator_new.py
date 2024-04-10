import csv
import random
from pathlib import Path

from cloud_guardian.iam_model.graph.permission import IAMAction
from cloud_guardian.iam_model.validating import ActionNotAllowedException, Validate


class State:
    def __init__(self, name):
        self.name = name
        self.transitions = {}
        self.actions = set()

    def add_transition(self, action, next_state):
        self.actions.add(action)
        if action in self.transitions:
            self.transitions[action].append(next_state)
        else:
            self.transitions[action] = [next_state]

    def get_allowed_actions(self):
        return list(self.actions)

    def get_valid_target_states(self, action):
        return self.transitions[action]


class Transition:
    def __init__(self, from_state, action, target_state):
        self.from_state = from_state
        self.action = action
        self.target_state = target_state


class PoliciesFSM:
    def __init__(self, num_entities, num_resources, constraints):
        # States are entities or resources
        self.states = {}
        # Transitions are the allowed actions between states
        self.all_transitions = []

        entity_types = list(Validate.get_valid_entities_str())
        resource_types = list(Validate.get_valid_resources_str())

        entities = [f"{random.choice(entity_types)}{i+1}" for i in range(num_entities)]
        resources = [
            f"{random.choice(resource_types)}_{i}" for i in range(num_resources)
        ]

        self.entities = entities
        self.resources = resources

        for entity in self.entities:
            for resource in self.resources:
                for action_name in constraints["actions"]:
                    action = IAMAction(action_name)
                    try:
                        Validate.edge(State(entity), State(resource), action)
                        if resource not in self.states:
                            self.states[resource] = State(resource)
                        if entity not in self.states:
                            self.states[entity] = State(entity)
                        self.states[entity].add_transition(action.name, resource)
                    except ActionNotAllowedException:
                        continue

        self.current_state = self.states[self.entities[0]]

    def set_random_entity(self):
        self.current_state = self.states[random.choice(self.entities)]

    def random_transition(self):
        current = self.current_state.name
        action = random.choice(self.current_state.get_allowed_actions())
        next_states = self.current_state.get_valid_target_states(action)
        if next_states:
            self.current_state = self.states[random.choice(next_states)]
            self.all_transitions.append(
                Transition(current, action, self.current_state.name)
            )
            return self.current_state.name

    def get_all_transitions(self):
        return self.all_transitions


def generate_fake_iam_policies(
    num_entities: int,
    num_resources: int,
    num_permissions: int,
    file_path: Path,
    constraints,
):
    random.seed(42)
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Condition", "SourceEntity", "Permission", "Target"])

        for _ in range(num_permissions):
            policies_FSM = PoliciesFSM(num_entities, num_resources, constraints)
            policies_FSM.set_random_entity()
            policies_FSM.random_transition()

            for transition in policies_FSM.get_all_transitions():
                condition = random.choice(list(Validate.get_valid_conditions_str()))
                writer.writerow(
                    [
                        condition,
                        transition.from_state,
                        transition.action,
                        transition.target_state,
                    ]
                )
