from enum import Enum


class Effect(Enum):
    ALLOW = "Allow"
    DENY = "Deny"

    def __str__(self):
        return self.value
