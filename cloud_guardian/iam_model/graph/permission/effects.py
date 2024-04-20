from enum import Enum, auto


class Effect(Enum):
    ALLOW = "Allow"
    DENY = "Deny"

    def __str__(self):
        return self.value
