from dataclasses import dataclass
from datetime import date
from typing import Protocol

from smallsteps.command_runner import CommandRunner
from smallsteps.ratchet import (
    Ratchet,
    RatchetEvaluation,
    RatchetEvaluationFailure,
    evaluate,
)


class DateProvider(Protocol):
    def __call__(self) -> date: ...


def local_system_date_provider() -> date:
    return date.today()


class StaticDateProvider(DateProvider):
    def __init__(self, date: date) -> None:
        self.date = date

    def __call__(self) -> date:
        return self.date


@dataclass(frozen=True)
class Prober:
    command_runner: CommandRunner
    date_provider: DateProvider

    def probe(self, ratchet: Ratchet) -> RatchetEvaluation:

        try:
            current_value = self.command_runner(ratchet)
            current_date = self.date_provider()

        except Exception as e:
            return RatchetEvaluationFailure(error_message=str(e))
        return evaluate(
            ratchet=ratchet, current_value=current_value, current_date=current_date
        )
