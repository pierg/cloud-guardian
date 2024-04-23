from cloud_guardian.iam_model.graph.graph import IAMGraph
from cloud_guardian.iam_model.graph.permission.actions import SupportedAction


class IAMGraphManager:
    def __init__(self, graph: IAMGraph):
        self.graph = graph

    def execute_action(self, source_id: str, action: SupportedAction, target_id: str = None):
        """Execute a supported action on the IAMGraph."""
        if target_id is None:
            target_id = source_id

        # Check if any edge exists between source and target and Relationship supports the action
        if self.graph.graph.has_edge(source_id, target_id):
            # get all relationships between source and target
            relationships = self.graph.graph[source_id][target_id]'
            supports = False
            for _, relationship_data in relationships.items():
                relationship = relationship_data.get('relationship')
                if relationship and relationship.supports_action(action):
                    supports = True
                    break
            if supports:
                # Execute the action based on the action type
                action_type = action.action_type
                if action_type == "AssumeRole":
                    return self.execute_assumerole(action, source_id)
                elif action_type == "AddUser":
                    return self.execute_adduser(action, source_id)
                elif action_type == "ModifyPermission":
                    return self.execute_modifypermission(action, source_id)
                else:
                    return self.unknown_action(action, source_id)

        else:
            raise ValueError(f"No relationship found between {source_id} and {target_id}")

        

    def execute_assumerole(self, action: SupportedAction, current_user: str):
        """Allows a user to assume a specified role, if a 'CanAssumeRole' relationship exists."""
        # Validate if there's a permissible edge for assuming role
        if self.graph.graph.has_edge(current_user, action.target_id):
            relationship = self.graph.graph[current_user][action.target_id].get('relationship')
            if isinstance(relationship, CanAssumeRole) and relationship.source.id == current_user:
                print(f"{current_user} is now assuming role {action.target_id}")
                return True
        print("Action not permitted to assume role.")
        return False

    def execute_adduser(self, action: SupportedAction, current_user: str):
        """Adds a new user to the IAMGraph if the current user has the permission to create users."""
        if self.has_permission(current_user, "CreateUser"):
            new_user = User(name=action.parameters['name'], arn=action.target_id, create_date=datetime.now())
            self.graph.add_node(action.target_id, new_user)
            print(f"New user {action.target_id} added by {current_user}.")
            return True
        print(f"{current_user} does not have permission to add users.")
        return False

    def execute_modifypermission(self, action: SupportedAction, current_user: str):
        """Modifies permissions of a user or role if allowed."""
        if self.has_permission(current_user, action.parameters.get('permission_id')):
            self.graph.graph.add_edge(current_user, action.target_id, relationship=action.parameters['new_permission'])
            print(f"Permission {action.parameters['permission_id']} modified by {current_user} for {action.target_id}")
            return True
        print(f"{current_user} does not have permission to modify permissions.")
        return False

    def has_permission(self, user_id, permission_id):
        """Checks if a user has a specific permission."""
        # Placeholder: Actual implementation would check for the correct 'HasPermission' relationship
        for _, _, edge_data in self.graph.graph.edges(data=True):
            if edge_data.get('relationship', None) and isinstance(edge_data['relationship'], HasPermission):
                if edge_data['relationship'].permission.id == permission_id:
                    return True
        return False

    def unknown_action(self, action: SupportedAction, current_user: str):
        """Fallback method if the action type is not recognized."""
        print(f"Action type {action.action_type} is not recognized.")
        return False
