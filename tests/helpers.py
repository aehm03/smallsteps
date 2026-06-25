from babysteps import CommandRunner, Ratchet


def create_ratchet(**kwargs) -> Ratchet:
    defaults = {
        "name": "test",
        "start": "2026-06-01",
        "end": "2026-06-01",
        "initial_value": 0,
        "goal_value": 10,
        "command": "echo 5",
    }
    return Ratchet(**(defaults | kwargs))


class FakeCommandRunner(CommandRunner):
    """CommandRunner that returns a fixed value given on init"""

    def __init__(self, value: int | float) -> None:
        self.value = value

    def __call__(self, ratchet: Ratchet) -> int | float:
        return self.value
