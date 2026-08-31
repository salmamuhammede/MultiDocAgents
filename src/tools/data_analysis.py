# Third Party
import json
from typing import Any, Annotated
from loguru import logger
from langchain_core.tools import tool


def _to_number(value: Any) -> float:
    """Convert a value to a number."""
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip().replace("%", "")

        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to a number.")

    raise ValueError(f"Unsupported numeric value: {value}")


def _extract_numeric_values(data: list[Any]) -> list[float]:
    """Extract numeric values from a list."""
    values = []

    for item in data:
        if isinstance(item, dict):
            # If the analyst passes {"value": 27.3}
            if "value" in item:
                values.append(_to_number(item["value"]))

        else:
            values.append(_to_number(item))

    if not values:
        raise ValueError("No numeric values were provided.")

    return values


@tool
def data_analysis(
    operation: str,
    data: list[Any],
    column: str | None = None,
) -> str:
    """
    Perform structured analysis on numerical or tabular data.

    Supported operations:
    - average
    - sum
    - minimum
    - maximum
    - difference
    - percentage
    - ranking
    - distribution

    Parameters:
        operation:
            The analysis operation to perform.

        data:
            Numerical values or structured records.

            Examples:

            [27.3, 38.1, 25.8]

            or:

            [
                {"model": "Transformer Base", "bleu": 27.3},
                {"model": "Transformer Big", "bleu": 28.4}
            ]

        column:
            The numerical column to analyze when data contains
            dictionaries.

    Returns:
        JSON string containing the analysis result.
    """
    logger.info("Called Data analysis tool")
    operation = operation.lower().strip()

    try:
        # ---------------------------------------------------------
        # Extract values from structured records if a column
        # was provided.
        # ---------------------------------------------------------

        if column is not None:
            values = []

            for row in data:
                if not isinstance(row, dict):
                    raise ValueError(
                        "When 'column' is provided, data must contain dictionaries."
                    )

                if column not in row:
                    raise ValueError(
                        f"Column '{column}' not found in row: {row}"
                    )

                values.append(_to_number(row[column]))

        else:
            values = _extract_numeric_values(data)

        # ---------------------------------------------------------
        # Average
        # ---------------------------------------------------------

        if operation == "average":
            result = sum(values) / len(values)

            output = {
                "operation": "average",
                "values": values,
                "count": len(values),
                "result": result,
            }

        # ---------------------------------------------------------
        # Sum
        # ---------------------------------------------------------

        elif operation == "sum":
            result = sum(values)

            output = {
                "operation": "sum",
                "values": values,
                "result": result,
            }

        # ---------------------------------------------------------
        # Minimum
        # ---------------------------------------------------------

        elif operation == "minimum":
            result = min(values)

            output = {
                "operation": "minimum",
                "values": values,
                "result": result,
            }

        # ---------------------------------------------------------
        # Maximum
        # ---------------------------------------------------------

        elif operation == "maximum":
            result = max(values)

            output = {
                "operation": "maximum",
                "values": values,
                "result": result,
            }

        # ---------------------------------------------------------
        # Difference
        # ---------------------------------------------------------

        elif operation == "difference":
            if len(values) < 2:
                raise ValueError(
                    "Difference requires at least two values."
                )

            result = max(values) - min(values)

            output = {
                "operation": "difference",
                "values": values,
                "maximum": max(values),
                "minimum": min(values),
                "result": result,
            }

        # ---------------------------------------------------------
        # Percentage
        # ---------------------------------------------------------

        elif operation == "percentage":
            if len(values) != 2:
                raise ValueError(
                    "Percentage operation requires exactly two values: "
                    "part and total."
                )

            part, total = values

            if total == 0:
                raise ValueError("Cannot calculate percentage with total = 0.")

            result = (part / total) * 100

            output = {
                "operation": "percentage",
                "part": part,
                "total": total,
                "result": result,
            }

        # ---------------------------------------------------------
        # Ranking
        # ---------------------------------------------------------

        elif operation == "ranking":
            if column is None:
                raise ValueError(
                    "Ranking requires structured records and a column."
                )

            ranked = sorted(
                data,
                key=lambda row: _to_number(row[column]),
                reverse=True,
            )

            output = {
                "operation": "ranking",
                "column": column,
                "ranking": [
                    {
                        "rank": index + 1,
                        **row,
                    }
                    for index, row in enumerate(ranked)
                ],
            }

        # ---------------------------------------------------------
        # Distribution
        # ---------------------------------------------------------

        elif operation == "distribution":
            output = {
                "operation": "distribution",
                "count": len(values),
                "minimum": min(values),
                "maximum": max(values),
                "average": sum(values) / len(values),
                "values": values,
            }

        else:
            raise ValueError(
                f"Unsupported operation: '{operation}'. "
                "Supported operations are: "
                "average, sum, minimum, maximum, difference, "
                "percentage, ranking, distribution."
            )

        return json.dumps(output, indent=2)

    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "operation": operation,
            },
            indent=2,
        )