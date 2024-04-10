class ActionNotAllowedException(Exception):
    def __init__(self, source, target, action):
        message = f"Action '{action.name}' is not allowed from '{source.__class__.__name__}' to '{target.__class__.__name__}'."
        super().__init__(message)
