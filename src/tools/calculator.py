from langchain_core.tools import tool
from loguru import logger


class Calculator:
    """A collection of mathematical tools for Analyst Agent."""

    @tool
    def basic_operation(operation: str, a: float, b: float) -> float:
        """Perform basic math. Operations: 'add', 'subtract', 'multiply', 'divide'."""
        operation = operation.lower()
        logger.info("Basic Operation called")
        if operation == "add":
            return a + b
        if operation == "subtract":
            return a - b
        if operation == "multiply":
            return a * b
        if operation == "divide":
            if b == 0:
                raise ValueError("Division by zero.")
            return a / b
        raise ValueError(f"Unknown operation: {operation}")

    @tool
    def percentage_change(old_value: float, new_value: float) -> float:
        """Calculate percentage improvement or difference between a baseline and a new value."""
        logger.info("Percent change Operation called")
        if old_value == 0:
            raise ValueError("Baseline cannot be zero.")
        return ((new_value - old_value) / old_value) * 100

    @tool
    def average(values: list[float]) -> float:
        """Calculate the arithmetic mean of a list of numeric values (e.g., model accuracies)."""
        logger.info("Averaging Operation called")
        if not values:
            raise ValueError("List cannot be empty.")
        return sum(values) / len(values)

    @tool
    def statistics(values: list[float]) -> dict:
        """Return a statistical summary including min, max, range, and average for a dataset."""
        logger.info("Statistical summary Operation called")
        if not values:
            raise ValueError("List cannot be empty.")
        return {
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "average": sum(values) / len(values),
        }
