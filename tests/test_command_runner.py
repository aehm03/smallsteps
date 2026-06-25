from babysteps.command_runner import CommandRunnerWithEnvLookUp, OSCommandRunner
from tests.helpers import FakeCommandRunner, create_ratchet

ENV_VALUE = 5
RUNNER_VALUE = 7


def fake_env_adapter(key: str) -> int | float:
    return ENV_VALUE


def test_command_runner_with_env_lookup_prefers_env():
    # given: command runner /w env lookup
    ratchet = create_ratchet()
    command_runner = CommandRunnerWithEnvLookUp(
        env_adapter=fake_env_adapter, command_runner=FakeCommandRunner(RUNNER_VALUE)
    )
    # when: its called and env available
    res = command_runner(ratchet=ratchet)
    #
    # then: env is preffered
    assert res == ENV_VALUE


def test_os_command_runner():
    # given: os command runner and ratchet with os comamand
    ratchet = create_ratchet(command="echo 50")
    command_runner = OSCommandRunner()
    # when: called
    res = command_runner(ratchet)
    # then: result is computed and parsed
    assert res == 50
