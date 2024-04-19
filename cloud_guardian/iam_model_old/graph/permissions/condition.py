import ipaddress
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Union

from cloud_guardian.utils.shared import constraints_conditions
from loguru import logger


@dataclass
class Condition:
    condition_key: str
    condition_operator: str
    condition_value: Any
    value_type: str

    @classmethod
    def validate_and_create(
        cls,
        condition_key: str,
        condition_operator: str,
        condition_value: str,
        value_type: str,
    ) -> "Condition":
        condition_type = next(
            (
                ct
                for ct in constraints_conditions
                if ct["condition_key"] == condition_key
            ),
            None,
        )

        if not condition_type:
            raise ValueError(f"Invalid condition key: {condition_key}")

        if condition_operator not in condition_type["operators"]:
            raise ValueError(
                f"Invalid operator for {condition_key}: {condition_operator}"
            )

        parsed_value = cls.parse_condition_value(condition_value, value_type)
        return cls(condition_key, condition_operator, parsed_value, value_type)

    @staticmethod
    def parse_condition_value(value_str: str, value_type: str) -> Any:
        try:
            if value_type == "cidr":
                return ipaddress.ip_network(value_str, strict=False)
            elif value_type == "time_range":
                # Ensure it matches time range pattern before proceeding
                if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", value_str):
                    raise ValueError("Invalid time range format. Expected HH:MM-HH:MM")
                start_str, end_str = value_str.split("-")
                return (
                    datetime.strptime(start_str, "%H:%M").time(),
                    datetime.strptime(end_str, "%H:%M").time(),
                )
            elif value_type == "integer":
                return int(value_str)
            else:
                return value_str
        except ValueError as e:
            logger.error(f"Error parsing condition value: {e}")
            raise

    def evaluate(self, context: Union[Dict[str, Any], None]) -> bool:
        if context is None:
            return True
        context_value = context.get(self.condition_key)
        if context_value is None:
            return False  # Condition key not found in context

        try:
            if self.value_type == "cidr":
                return ipaddress.ip_address(context_value) in self.condition_value
            elif self.value_type == "time_range":
                if not isinstance(context_value, datetime.time):
                    context_time = datetime.strptime(context_value, "%H:%M").time()
                else:
                    context_time = context_value
                start_time, end_time = self.condition_value
                return start_time <= context_time <= end_time
            elif self.value_type == "integer":
                if self.condition_operator == "equals":
                    return context_value == self.condition_value
                elif self.condition_operator == "not_equals":
                    return context_value != self.condition_value
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

        # Extend with more conditions as necessary
        return False


def show_usage():
    def mock_validate_and_create(
        condition_key, condition_operator, condition_value, value_type
    ):
        return Condition(
            condition_key,
            condition_operator,
            Condition.parse_condition_value(condition_value, value_type),
            value_type,
        )

    # Creating conditions
    ip_condition = mock_validate_and_create(
        "ipAddress", "in_range", "192.168.1.0/24", "cidr"
    )
    time_condition = mock_validate_and_create(
        "loginTime", "time_between", "09:00-17:00", "time_range"
    )
    user_condition = mock_validate_and_create("userId", "equals", "42", "integer")

    # Contexts to test
    ip_context_true = {"ipAddress": "192.168.1.15"}
    ip_context_false = {"ipAddress": "192.168.2.1"}

    time_context_true = {"loginTime": "10:30"}
    time_context_false = {"loginTime": "18:00"}

    user_context_true = {"userId": 42}
    user_context_false = {"userId": 100}

    # Evaluating conditions
    print("IP Condition (True expected):", ip_condition.evaluate(ip_context_true))
    print("IP Condition (False expected):", ip_condition.evaluate(ip_context_false))

    print("Time Condition (True expected):", time_condition.evaluate(time_context_true))
    print(
        "Time Condition (False expected):", time_condition.evaluate(time_context_false)
    )

    print("User Condition (True expected):", user_condition.evaluate(user_context_true))
    print(
        "User Condition (False expected):", user_condition.evaluate(user_context_false)
    )


# show_usage()
