from typing import Any


def parse_numeric_input(value: Any) -> int | float:
    if isinstance(value, (int, float)):
        return value

    if not isinstance(value, str):
        raise TypeError(f"Expected string or number, got {type(value).__name__}")

    cleaned = value.strip()

    # Elegant trick: Change "99.5%" to "99.5e-2" (scientific notation for /100)
    if cleaned.endswith("%"):
        return float(cleaned.rstrip("%").strip() + "e-2")

    # Standard fallback path (int takes priority to preserve type fidelity)
    try:
        return int(cleaned)
    except ValueError:
        try:
            return float(cleaned)
        except ValueError:
            raise ValueError(f"Could not parse string '{value}' into a number.")
