from datetime import date, timedelta
from pathlib import Path

from typer.testing import CliRunner

from smallsteps.cli import app

runner = CliRunner()


def test_add_and_check_decreasing_int_failure(tmp_path: Path):
    """
    E2E Case 1: Decreasing Ratchet with Integers (Expected Failure at Midpoint).

    Timeline Setup:
      - Start (Today): 100 open issues
      - End (Today + 10 days): 0 open issues
      - Check Date (Today + 5 days): Expected target milestone is 50.00.
      - Command Output: 100.00 (Fails because 100 > 50 allowed max).
    """
    config_file = tmp_path / "smallsteps.toml"
    today = date.today()
    end_date = today + timedelta(days=10)
    check_date = today + timedelta(days=5)

    # 1. Add the decreasing int ratchet
    add_result = runner.invoke(
        app,
        [
            "add",
            "--name",
            "Open Architecture Issues",
            "--command",
            "echo '100'",
            "--goal",
            "0",
            "--end",
            end_date.isoformat(),
            "--config",
            str(config_file),
        ],
    )
    assert add_result.exit_code == 0

    # 2. Enforce check at the milestone midpoint
    check_result = runner.invoke(
        app, ["check", "--config", str(config_file), "--date", check_date.isoformat()]
    )

    assert check_result.exit_code == 1
    assert "BEHIND" in check_result.output
    assert "Current: 100.00" in check_result.output
    assert "Expected Min: 50.00" in check_result.output
    assert "Progress check failed." in check_result.output


def test_add_and_check_increasing_float_success(tmp_path: Path):
    """
    E2E Case 2: Increasing Ratchet with Native Floats (Expected Success on Day Zero).

    Timeline Setup:
      - Start (Today): 56.7 speed metric
      - End (Today + 10 days): 80.0 speed metric
      - Check Date (Today / Day Zero): Expected target milestone is exactly 56.70.
      - Command Output: 56.70 (Passes cleanly because 56.7 >= 56.7 requirement).
    """
    config_file = tmp_path / "smallsteps.toml"
    today = date.today()
    end_date = today + timedelta(days=10)

    # 1. Add the increasing float ratchet
    add_result = runner.invoke(
        app,
        [
            "add",
            "--name",
            "Performance Index",
            "--command",
            "echo '56.7'",
            "--goal",
            "80.0",
            "--end",
            end_date.isoformat(),
            "--config",
            str(config_file),
        ],
    )
    assert add_result.exit_code == 0

    # 2. Enforce check immediately on Day Zero
    check_result = runner.invoke(
        app, ["check", "--config", str(config_file), "--date", today.isoformat()]
    )

    assert check_result.exit_code == 0
    assert "ON TRACK" in check_result.output
    assert "Current: 56.70" in check_result.output
    assert "Expected Min: 56.70" in check_result.output
    assert (
        "All monitored project metrics are completely healthy." in check_result.output
    )


def test_add_and_check_decreasing_percentage_failure(tmp_path: Path):
    """
    E2E Case 3: Decreasing Ratchet with Percentages (Expected Failure at Midpoint).

    Timeline Setup:
      - Start (Today): 90% error rate
      - End (Today + 10 days): 0% error rate
      - Check Date (Today + 5 days): Expected target milestone is 45.00.
      - Command Output: 90.00 (Fails because 90 > 45 allowed max).
    """
    config_file = tmp_path / "smallsteps.toml"
    today = date.today()
    end_date = today + timedelta(days=10)
    check_date = today + timedelta(days=5)

    # 1. Add the decreasing percentage ratchet
    add_result = runner.invoke(
        app,
        [
            "add",
            "--name",
            "Lint Error Rate",
            "--command",
            "echo '90%'",
            "--goal",
            "0%",
            "--end",
            end_date.isoformat(),
            "--config",
            str(config_file),
        ],
    )
    assert add_result.exit_code == 0

    # 2. Enforce check at the milestone midpoint
    check_result = runner.invoke(
        app, ["check", "--config", str(config_file), "--date", check_date.isoformat()]
    )

    assert check_result.exit_code == 1
    assert "BEHIND" in check_result.output
    assert "Current: 0.90" in check_result.output
    assert "Expected Min: 0.45" in check_result.output
    assert "Progress check failed." in check_result.output

def test_add_multiple_ratchets_appends_successfully(tmp_path: Path):
    """
    E2E Test: Verifies that calling 'add' multiple times sequentially
    correctly appends multiple discrete [[ratchets]] configuration blocks
    to smallsteps.toml instead of overwriting the file.
    """
    config_file = tmp_path / "smallsteps.toml"
    end_date_str = (date.today() + timedelta(days=10)).isoformat()

    # 1. Add the first unique ratchet metric
    first_add = runner.invoke(
        app,
        [
            "add",
            "--name", "Pytest Coverage",
            "--command", "echo '55.0'",
            "--goal", "80.0",
            "--end", end_date_str,
            "--config", str(config_file)
        ]
    )
    assert first_add.exit_code == 0
    assert "Successfully added" in first_add.output

    # 2. Add a second completely distinct ratchet metric to the same config path
    second_add = runner.invoke(
        app,
        [
            "add",
            "--name", "Type Baseline Tracker",
            "--command", "echo '10'",
            "--goal", "0",
            "--end", end_date_str,
            "--config", str(config_file)
        ]
    )
    assert second_add.exit_code == 0
    assert "Successfully added" in second_add.output

    # 3. Read raw file content to verify multiple block structures exist textually
    file_content = config_file.read_text(encoding="utf-8")
    assert file_content.count("[[ratchets]]") == 2
    assert 'name = "Pytest Coverage"' in file_content
    assert 'name = "Type Baseline Tracker"' in file_content

    # 4. Run the 'check' command to verify both are loaded and evaluated together
    check_result = runner.invoke(
        app,
        [
            "check",
            "--config", str(config_file),
            "--date", date.today().isoformat()
        ]
    )

    # Both echo commands return their baseline matches on Day Zero -> Clean execution
    assert check_result.exit_code == 0
    assert "Evaluating 2 ratchet(s)..." in check_result.output
    assert "Pytest Coverage: ON TRACK" in check_result.output
    assert "Type Baseline Tracker: ON TRACK" in check_result.output
