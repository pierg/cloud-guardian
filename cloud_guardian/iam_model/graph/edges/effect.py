from enum import Enum, auto


class Effect(Enum):
    ALLOW = auto()
    DENY = auto()

    @classmethod
    def from_string(cls, effect_str: str):
        """Converts a string, possibly containing '~', to an Effect instance."""
        if effect_str.startswith("~"):
            return cls.DENY
        else:
            return cls.ALLOW

    def to_symbol(self) -> str:
        """Returns a symbolic string representation of the effect ('~' for DENY, empty string for ALLOW)."""
        if self == self.DENY:
            return "~"
        return ""

    def __str__(self) -> str:
        """Optional: Override the string representation to use the symbolic representation."""
        return self.to_symbol()
