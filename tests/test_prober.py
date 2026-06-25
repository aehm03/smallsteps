from babysteps.prober import Prober, StaticDateProvider
from babysteps.ratchet import Ratchet
from tests.helpers import FakeCommandRunner, create_ratchet


def failing_command_runner(ratchet: Ratchet) -> int | float:
    raise RuntimeError()


def test_prober_fails_if_value_can_not_be_acquired():
    # given: a prober and a ratchet

    zero_to_ten_ratchet: Ratchet = create_ratchet()
    prober = Prober(
        command_runner=failing_command_runner,
        date_provider=StaticDateProvider(zero_to_ten_ratchet.end),
    )
    # when: it is probed but the value is not available
    evaluation = prober.probe(zero_to_ten_ratchet)

    # then: it is not healthy
    assert not evaluation.is_healthy


def test_prober_succeds_if_goal_is_met():
    # given: a prober and a ratchet
    zero_to_ten_ratchet: Ratchet = create_ratchet()
    prober = Prober(
        command_runner=FakeCommandRunner(10),
        date_provider=StaticDateProvider(zero_to_ten_ratchet.end),
    )
    # when: it is probed
    evaluation = prober.probe(zero_to_ten_ratchet)

    # then: it is not healthy
    assert evaluation.is_healthy
