import re
from typing import List
from dataclasses import dataclass, field
from loguru import logger

@dataclass
class SpecifiedActions:
    aws_action_pattern: str
    _regex_pattern: str = field(init=False, repr=False)

    def __post_init__(self):
        self._regex_pattern = '^' + self.aws_action_pattern.replace('*', '.*') + '$'

    def matches(self, action: str) -> bool:
        """
        Checks if a given action matches the specified AWS action pattern.
        """
        return re.match(self._regex_pattern, action) is not None

    def find_matching_actions(self, actions: List[str]) -> List[str]:
        """
        Returns all actions from a list that match the specified AWS action pattern.
        """
        logger.debug(f"Finding actions that match pattern: {self.aws_action_pattern} among {actions}")
        return [action for action in actions if self.matches(action)]
    
    @property
    def id(self):
        return self.aws_action_pattern
    
    def __str__(self):
        return self.aws_action_pattern

class ActionsFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, aws_action_pattern: str) -> SpecifiedActions:
        """
        Retrieves an existing SpecifiedActions object for the given action pattern or creates a new one if it does not exist.
        """
        if aws_action_pattern not in cls._instances:
            cls._instances[aws_action_pattern] = SpecifiedActions(aws_action_pattern)
        return cls._instances[aws_action_pattern]
