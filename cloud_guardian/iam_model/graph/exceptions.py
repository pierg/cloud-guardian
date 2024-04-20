
class ActionNotSupported(Exception):
    def __init__(self, action):
        self.action = action
        self.message = f"Action {action} is not supported"
        super().__init__(self.message)


class ConditionNotSupported(Exception):
    def __init__(self, condition):
        self.condition = condition
        self.message = f"Condition {condition} is not supported"
        super().__init__(self.message)