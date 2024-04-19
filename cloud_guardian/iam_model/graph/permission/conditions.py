from dataclasses import dataclass
from typing import Any, Union
from datetime import datetime

@dataclass(frozen=True)
class SupportedCondition:
    condition_value: Union[str, list, dict]
    condition_key: str
    condition_operator: str
    value_type: str

    def __str__(self):
        return f"{self.condition_key} {self.condition_operator} {self.condition_value}"

    def evaluate(self, runtime_value: Any) -> bool:
        raise NotImplementedError("Subclasses must implement this method.")

@dataclass(frozen=True)
class DateGreaterThan(SupportedCondition):
    condition_value: str
    condition_key: str = "aws:CurrentTime"
    condition_operator: str = "DateGreaterThan"
    value_type: str = "Date"

    def evaluate(self, runtime_value: str) -> bool:
        condition_date = datetime.fromisoformat(self.condition_value)
        runtime_date = datetime.fromisoformat(runtime_value)
        return runtime_date > condition_date

@dataclass(frozen=True)
class IpAddress(SupportedCondition):
    condition_value: Union[str, list]
    condition_key: str = "aws:SourceIp"
    condition_operator: str = "IpAddress"
    value_type: str = "IPAddress"

    def evaluate(self, runtime_value: str) -> bool:
        from ipaddress import ip_address, ip_network
        if isinstance(self.condition_value, list):
            return any(ip_address(runtime_value) in ip_network(ip) for ip in self.condition_value)
        return ip_address(runtime_value) in ip_network(self.condition_value)
    

class ConditionFactory:
    _condition_map = {
        "DateGreaterThan": DateGreaterThan,
        "IpAddress": IpAddress
    }

    @classmethod
    def create_condition(cls, condition_dict):
        for condition_type, details in condition_dict.items():
            if condition_type in cls._condition_map:
                condition_key, value = next(iter(details.items()))
                condition_class = cls._condition_map[condition_type]
                return condition_class(condition_key=condition_key, condition_operator=condition_type, condition_value=value, value_type=cls._infer_type(value))
            else:
                raise ValueError(f"Condition '{condition_type}' is not supported.")

    @staticmethod
    def _infer_type(value):
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value)
                return "Date"
            except ValueError:
                return "String"
        elif isinstance(value, list) or isinstance(value, dict):
            return "List"
