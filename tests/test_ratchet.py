import datetime

import pytest

from smallsteps.ratchet import evaluate
from tests.helpers import create_ratchet


def test_ratchet_end_date_is_after_start_date():
    # given: a ratchet construction instruction
    # when: the end date is before the start date
    # then: a value error is raised

    with pytest.raises(ValueError):
        create_ratchet(
            start="2026-06-01",
            end="2026-05-01",
        )


def test_ratchet_with_equal_start_and_end_date_is_valid():
    """
    Setting the start and end date of the ratched is equivalent to saying
    'The goal should be met now', which is valid
    """
    # given: a ratchet construction instruction
    # when: the end date is equal to the start date
    # then: it is constructed
    create_ratchet(start="2026-06-01", end="2026-06-01")


def test_ratchet_has_a_goal_value():
    # given: a ratchet construction instruction
    # when: the goal is equal to the start value
    # then: a value error is raised
    with pytest.raises(ValueError):
        create_ratchet(initial_value=10, goal_value=10)


def test_after_end_date_goal_value_must_be_met():
    # given: a Ratchet
    zero_to_ten_ratchet = create_ratchet()
    # when: it is checked after the end date
    under_goal = evaluate(
        zero_to_ten_ratchet,
        current_value=5,
        current_date=datetime.datetime.strptime("2026-06-02", "%Y-%m-%d").date(),
    )
    at_goal = evaluate(
        zero_to_ten_ratchet,
        current_value=10,
        current_date=datetime.datetime.strptime("2026-06-02", "%Y-%m-%d").date(),
    )

    # then: the goal must be met
    assert not under_goal.is_healthy
    assert at_goal.is_healthy


def test_decreasing_ratchet_goal_must_be_met():
    # given a decreasing value ratchet
    ratchet = create_ratchet(initial_value=10, goal_value=5)

    # when it is evaluated after the goal date
    no_goal = evaluate(
        ratchet,
        current_value=7,
        current_date=datetime.datetime.strptime("2026-06-02", "%Y-%m-%d").date(),
    )
    goal = evaluate(
        ratchet,
        current_value=3,
        current_date=datetime.datetime.strptime("2026-06-02", "%Y-%m-%d").date(),
    )

    # then it must be evaluated to true if the goal is met / false else
    assert not no_goal.is_healthy
    assert goal.is_healthy
