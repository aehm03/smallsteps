from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator
from typing_extensions import Self


class Ratchet(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    start: date
    end: date
    initial_value: int | float
    goal_value: int | float
    command: str

    @model_validator(mode="after")
    def validate_end(self) -> Self:
        if self.end < self.start:
            raise ValueError("End date must be >= start date of ratchet")
        return self

    @model_validator(mode="after")
    def validate_value(self) -> Self:
        if self.initial_value == self.goal_value:
            raise ValueError("Initial value must be different from goal")
        return self


@dataclass(frozen=True)
class RatchetEvaluationSuccess:
    current_date: date
    current_value: int | float
    expected_value: float
    is_healthy: bool


@dataclass(frozen=True)
class RatchetEvaluationFailure:
    error_message: str
    is_healthy: bool = False


RatchetEvaluation = RatchetEvaluationSuccess | RatchetEvaluationFailure


def evaluate(
    ratchet: Ratchet, current_value: int | float, current_date: date
) -> RatchetEvaluation:
    if current_date <= ratchet.start:
        time_ratio = 0.0
    elif current_date >= ratchet.end:
        time_ratio = 1.0
    else:
        time_ratio = (current_date - ratchet.start).days / (
            ratchet.end - ratchet.start
        ).days

    expected_progress = time_ratio  # linear progress assumed
    expected_value = ratchet.initial_value + (
        expected_progress * (ratchet.goal_value - ratchet.initial_value)
    )
    actual_progress = (current_value - ratchet.initial_value) / (
        ratchet.goal_value - ratchet.initial_value
    )
    return RatchetEvaluationSuccess(
        current_date=current_date,
        current_value=current_value,
        expected_value=expected_value,
        is_healthy=actual_progress >= expected_progress,
    )
