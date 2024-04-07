from enum import Enum, auto
import random
import csv
from pathlib import Path


PERMISSIONS = ["Read", "Write", "Full_Control", "Execute"]
CONDITIONS = ["", "IpAddress==192.168.1.1", "Time==09:00-17:00"]
RESOURCES = ["Datastore", "Compute"]


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
    """
    A random Finite State Machine to generate test data
    that complies with the policy framework
    """

    def __init__(self, num_entities, num_resources):
        self.states = {}
        self.all_transitions = []

        users = [f"User{i+1}" for i in range(random.randint(1, num_entities // 2))]
        remaining = num_entities - len(users)
        groups = [f"Group{i+1}" for i in range(random.randint(1, remaining // 2))]
        roles = [f"Role{i+1}" for i in range(remaining - len(groups))]

        self.entities = [
            element for sublist in [users, groups, roles] for element in sublist
        ]
        self.resources = [
            f"{resource}_{i}" for resource in RESOURCES for i in range(num_resources)
        ]

        # list of allowed transitions
        # 1) transitions entity -[permission]-> resource
        for entity in self.entities:
            for resource in self.resources:
                for permission in PERMISSIONS:
                    if resource not in self.states:
                        self.states[resource] = State(resource)
                    if entity not in self.states:
                        self.states[entity] = State(entity)
                    self.states[entity].add_transition(permission, resource)

        # 2) transitions users -[part of]-> groups
        for user in users:
            for group in groups:
                self.states[user].add_transition("Part_Of", group)

        # 3) transitions users+groups -[assume role]-> groups
        for user in users:
            for group in groups:
                for role in roles:
                    self.states[user].add_transition("Assume_Role", role)
                    self.states[group].add_transition("Assume_Role", role)

        # set first entity by default
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
    num_entities: int, num_resources: int, num_permissions: int, file_path: Path
):
    random.seed(42)
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Condition", "SourceEntity", "Permission", "Target"])

        for i in range(num_permissions):
            policies_FSM = PoliciesFSM(num_entities, num_resources)

            # set a random starting entity
            policies_FSM.set_random_entity()

            # set a random transition to reach a random target
            policies_FSM.random_transition()

            for transition in policies_FSM.get_all_transitions():
                writer.writerow(
                    [
                        random.choice(CONDITIONS),
                        transition.from_state,
                        transition.action,
                        transition.target_state,
                    ]
                )
