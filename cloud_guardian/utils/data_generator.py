import csv
import random
from pathlib import Path


def generate_fake_iam_policies(
    num_nodes: int, num_resources: int, num_permissions: int, file_path: Path
):
    random.seed(42)  # For reproducibility in examples

    # Split num_nodes randomly into users, groups, and roles
    users = [f"User{i+1}" for i in range(random.randint(1, num_nodes // 2))]
    remaining = num_nodes - len(users)
    groups = [f"Group{i+1}" for i in range(random.randint(1, remaining // 2))]
    roles = [f"Role{i+1}" for i in range(remaining - len(groups))]

    # Define resources with a randomized type
    resources = [
        f"{random.choice(['Datastore', 'Compute'])}{i+1}" for i in range(num_resources)
    ]

    # Entity-Resource Actions
    resources_permissions = ["Read", "Write", "Full_Control", "Execute"]

    # Entity-entity Actions
    entity_permissions = ["Part_Of", "Assume_Role"]

    # Conditions
    conditions = ["", "IpAddress==192.168.1.1", "Time==09:00-17:00"]

    # Writing to CSV
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Condition", "SourceEntity", "Permission", "Target"])

        for _ in range(num_permissions):
            # Decide between entity-resource or entity-entity action
            if random.choice([True, False]):
                source = random.choice(users + groups + roles)
                target = random.choice(resources)
                permission = random.choice(resources_permissions)
            else:
                if random.choice([True, False]):  # Part_Of or Assume_Role
                    # Part_Of can only be from User to Group
                    source = random.choice(users)
                    target = random.choice(groups)
                    permission = "Part_Of"
                else:  # Assume_Role
                    # Assume_Role can be from User/Group to Role
                    source = random.choice(users + groups)
                    target = random.choice(roles)
                    permission = "Assume_Role"

            condition = random.choice(conditions)
            writer.writerow([condition, source, permission, target])
