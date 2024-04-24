import re
from dataclasses import dataclass, field
from typing import List



@dataclass
class SpecifiedActions:
    aws_action_pattern: str
    _regex_pattern: str = field(init=False, repr=False)

    def __post_init__(self):
        # Convert the AWS action pattern to a regular expression pattern.
        # This involves escaping special characters in regex, replacing "*" with ".*" to match any sequence of characters.
        escaped_pattern = re.escape(self.aws_action_pattern).replace(r"\*", ".*")
        self._regex_pattern = f"^{escaped_pattern}$"

    def matches(self, action: str) -> bool:
        """
        Checks if a given action matches the specified AWS action pattern using a regex.
        """
        match_found = re.fullmatch(self._regex_pattern, action) is not None
        return match_found

    def find_matching_actions(self, actions: List[str]) -> List[str]:
        """
        Returns all actions from a list that match the specified AWS action pattern.
        """
        matching_actions = [action for action in actions if self.matches(action)]
        return matching_actions

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
