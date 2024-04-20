from dataclasses import dataclass
from typing import Any, Union
from datetime import datetime
import hashlib

from cloud_guardian.iam_model.graph.exceptions import ConditionNotSupported


@dataclass(frozen=True)
class SupportedCondition:
    id: str
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
class DateLessThan(SupportedCondition):
    condition_value: str
    condition_key: str = "aws:CurrentTime"
    condition_operator: str = "DateLessThan"
    value_type: str = "Date"

    def evaluate(self, runtime_value: str) -> bool:
        condition_date = datetime.fromisoformat(self.condition_value)
        runtime_date = datetime.fromisoformat(runtime_value)
        return runtime_date < condition_date


@dataclass(frozen=True)
class IpAddress(SupportedCondition):
    condition_value: Union[str, list]
    condition_key: str = "aws:SourceIp"
    condition_operator: str = "IpAddress"
    value_type: str = "IPAddress"

    def evaluate(self, runtime_value: str) -> bool:
        from ipaddress import ip_address, ip_network

        if isinstance(self.condition_value, list):
            return any(
                ip_address(runtime_value) in ip_network(ip)
                for ip in self.condition_value
            )
        return ip_address(runtime_value) in ip_network(self.condition_value)


class ConditionFactory:
    _instances = {}
    _condition_map = {
        "DateGreaterThan": DateGreaterThan,
        "IpAddress": IpAddress,
        "DateLessThan": DateLessThan,
    }

    @classmethod
    def from_dict(cls, condition_dict):
        condition_type, details = next(iter(condition_dict.items()))
        if condition_type not in cls._condition_map:
            raise ConditionNotSupported(condition_type)

        condition_key, value = next(iter(details.items()))
        condition_id = cls._create_id(condition_type, condition_key, value)

        if condition_id not in cls._instances:
            condition_class = cls._condition_map[condition_type]
            condition_instance = condition_class(
                id=condition_id,
                condition_key=condition_key,
                condition_operator=condition_type,
                condition_value=value,
                value_type=cls._infer_type(value),
            )
            cls._instances[condition_id] = condition_instance
        return cls._instances[condition_id]

    @staticmethod
    def _create_id(condition_type, condition_key, value):
        combined = f"{condition_type}{condition_key}{value}"
        return hashlib.sha256(combined.encode()).hexdigest()

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
