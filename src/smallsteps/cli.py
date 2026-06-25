from datetime import date, datetime, timedelta
from pathlib import Path

import typer

from smallsteps.ci_adapter import GitHubCIAdapter
from smallsteps.cli_helpers import find_git_root
from smallsteps.command_runner import (
    CommandRunnerWithEnvLookUp,
    OSCommandRunner,
    OSEnvAdapter,
)
from smallsteps.config_adapter import TOMLConfigAdapter
from smallsteps.parsing import parse_numeric_input
from smallsteps.prober import Prober, StaticDateProvider, local_system_date_provider
from smallsteps.ratchet import (
    Ratchet,
    RatchetEvaluationFailure,
    RatchetEvaluationSuccess,
)

app = typer.Typer(
    help="Smallsteps: Monotonic progress tracking and enforcement.",
    no_args_is_help=True,
)

DEFAULT_CONFIG_FILE = Path("smallsteps.toml")


def resolve_config_path(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        return explicit_path
    return find_git_root() / DEFAULT_CONFIG_FILE


@app.command(name="add")
def add(
    name: str = typer.Option(
        None, "--name", "-n", help="Unique name for your ratchet."
    ),
    goal_val: str = typer.Option(
        None, "--goal", "-g", help="Goal value (e.g. .9 or 250)."
    ),
    command_str: str = typer.Option(
        None, "--command", "-cmd", help="Shell command to compute the value."
    ),
    end_date: datetime | None = typer.Option(
        None, "--end", "-e", help="Ratchet goal end date (YYYY-MM-DD)."
    ),
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Custom path to config file."
    ),
):
    """Adds a ratchet to your configuration (Auto-creates smallsteps.toml if missing)."""
    config_path = resolve_config_path(config)
    config_adapter = TOMLConfigAdapter()

    # 1. Collect or prompt for the name first
    final_name = name or typer.prompt("Ratchet name (e.g., Test Coverage)")

    existing_ratchets = config_adapter.load(config_path)
    if any(r.name == final_name for r in existing_ratchets):
        typer.secho(
            f"❌ A ratchet named '{final_name}' already exists.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # 2. Ask for command and use it for baseline
    final_cmd = command_str or typer.prompt(
        "Shell command to compute the ratchet value"
    )
    typer.echo("Running command to establish live baseline value...")
    runner = OSCommandRunner()
    try:
        # Create a temporary Ratchet instance to satisfy our runner protocol
        temp_ratchet = Ratchet(
            name=final_name,
            start=date.today(),
            end=date.today(),
            initial_value=0,
            goal_value=100,
            command=final_cmd,
        )
        discovered_baseline = runner(temp_ratchet)

    except Exception as e:
        typer.secho(
            f"❌ Failed to calculate baseline using that command.\nError: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(f"Live baseline discovered: {discovered_baseline:.2f}")
    # 3. Ask for the Goal
    raw_goal = goal_val or typer.prompt(
        f"What is your goal value? (Current: {discovered_baseline})"
    )

    try:
        final_goal = parse_numeric_input(raw_goal)
    except ValueError as e:
        typer.secho(f"❌ Invalid goal value: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # 4. Handle Target Goal Date
    if end_date:
        final_end_date = end_date.date()
    else:
        goal_date_str = typer.prompt(
            f"What is the end date by which the goal must be met? (YYYY-MM-DD, e.g. in 30 days its {(date.today() + timedelta(days=30)).isoformat()} ) ",
        )
        try:
            final_end_date = date.fromisoformat(goal_date_str)
        except ValueError:
            typer.secho(
                f"❌ Invalid date format '{goal_date_str}'. Please use YYYY-MM-DD.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

    # 5. Construct Ratchet
    try:
        validated_ratchet = Ratchet(
            name=final_name,
            start=date.today(),
            end=final_end_date,
            initial_value=discovered_baseline,
            goal_value=final_goal,
            command=final_cmd,
        )
    except Exception as e:
        typer.secho(
            f"❌ Ratchet validation failed:\n{e}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1)

    # 6. Write
    config_adapter.append(config_path, validated_ratchet)
    typer.secho(
        f"✨ Successfully added '{validated_ratchet.name}' to {config_path.name}!",
        fg=typer.colors.GREEN,
    )


@app.command(name="check")
def check(
    date: datetime | None = typer.Option(
        None,
        "--date",
        "-d",
        help="Timetravel to a specific date to check your ratchets at.",
    ),
    config: Path | None = typer.Option(None, "--config", "-c"),
):
    """Evaluates all ratchets and enforces progress."""
    config_path = resolve_config_path(config)
    config_adapter = TOMLConfigAdapter()

    try:
        ratchets = config_adapter.load(config_path)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if not ratchets:
        typer.secho(
            f"No active ratchets found in {config_path.name}.",
            fg=typer.colors.YELLOW,
        )
        return

    # Wire up runner & prober pipeline
    runner_with_lookup = CommandRunnerWithEnvLookUp(
        env_adapter=OSEnvAdapter(), command_runner=OSCommandRunner()
    )
    date_provider = (
        StaticDateProvider(date.date()) if date else local_system_date_provider
    )
    prober = Prober(command_runner=runner_with_lookup, date_provider=date_provider)

    any_failed = False
    typer.echo(f"Evaluating {len(ratchets)} ratchet(s)...\n")

    for ratchet in ratchets:
        eval_result = prober.probe(ratchet)

        match eval_result:
            # TRACK 1: Metric is completely healthy and on track
            case RatchetEvaluationSuccess(is_healthy=True) as success:
                typer.secho(
                    f"{ratchet.name}: ON TRACK "
                    f"(Current: {success.current_value:.2f}, Expected Min: {success.expected_value:.2f})",
                    fg=typer.colors.GREEN,
                )

            # TRACK 2: Command executed fine, but progress dropped below expected target bounds
            case RatchetEvaluationSuccess(is_healthy=False) as below:
                any_failed = True
                typer.secho(
                    f"{ratchet.name}: BEHIND "
                    f"(Current: {below.current_value:.2f}, Expected Min: {below.expected_value:.2f})",
                    fg=typer.colors.RED,
                )

            # TRACK 3: Underlying shell execution exploded completely (command error, timeout, missing binary)
            case RatchetEvaluationFailure() as failure:
                any_failed = True

                typer.secho(
                    f"{ratchet.name} EVALUATION FAILED! \n"
                    f"Details: {failure.error_message}",
                    fg=typer.colors.RED,
                    err=True,
                )

    if any_failed:
        typer.echo("\nProgress check failed.")
        raise typer.Exit(code=1)

    typer.echo("All monitored project metrics are completely healthy.")


@app.command(name="ci")
def ci(
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Force overwrite the action.yaml file if it already exists.",
    ),
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Custom path to the smallsteps configuration file."
    ),
):
    """Generates a scaffoling for a github action"""
    config_path = resolve_config_path(config)
    config_adapter = TOMLConfigAdapter()
    ci_adapter = GitHubCIAdapter()

    # 1. Check if the target file destination already exists
    action_path = Path(".github/actions/smallsteps/action.yaml")
    if action_path.exists() and not overwrite:
        typer.secho(
            f"Action manifest already exists at:\n   {action_path.resolve()}\n\n"
            f"To overwrite this file, re-run this command with the overwrite flag:\n"
            f"uv run smallsteps ci --overwrite",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # 2. Extract configuration records
    try:
        ratchets = config_adapter.load(config_path)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # 3. Process layout formatting maps
    yaml_content = ci_adapter.generate_action(ratchets)

    # 4. Save out structural changes
    try:
        ci_adapter.save(action_path, yaml_content)
        typer.secho(
            f"🚀 Custom GitHub Composite Action successfully written to:\n   {action_path}",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
