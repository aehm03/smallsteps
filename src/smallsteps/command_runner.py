import os
import re
import subprocess
from typing import Optional, Protocol

from smallsteps.parsing import parse_numeric_input
from smallsteps.ratchet import Ratchet


def ratchet_to_slug(ratchet: Ratchet) -> str:
    clean_name = re.sub(r"[^a-zA-Z0-9]", "_", ratchet.name).upper()
    return f"SMALLSTEPS_{clean_name}"


class EnvAdapter(Protocol):
    def __call__(self, key: str) -> int | float | None: ...


class CommandRunner(Protocol):
    def __call__(self, ratchet: Ratchet) -> int | float: ...


class OSCommandRunner(CommandRunner):
    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    def __call__(self, ratchet: Ratchet) -> int | float:
        # Guard against empty commands
        if not ratchet.command or not ratchet.command.strip():
            raise ValueError(
                f"Ratchet '{ratchet.name}' has an empty or missing command string."
            )

        try:
            # Execute the shell command
            result = subprocess.run(
                ratchet.command,
                shell=True,
                capture_output=True,  # Captures stdout and stderr
                text=True,  # Returns strings instead of bytes
                timeout=self.timeout_seconds,  # Prevents hanging infinitely in CI
                check=True,  # Raises CalledProcessError if exit code != 0
            )

            # Extract, clean, and parse the output
            raw_output = result.stdout.strip()
            return parse_numeric_input(raw_output)

        except subprocess.TimeoutExpired as e:
            # Enrich the timeout error with explicit context
            raise RuntimeError(
                f"Command timed out after {self.timeout_seconds}s: '{ratchet.command}'"
            ) from e

        except subprocess.CalledProcessError as e:
            error_details = e.stderr.strip() or e.stdout.strip() or "No output logged."
            raise RuntimeError(
                f"Command failed with exit code {e.returncode}.\n"
                f"Command: '{ratchet.command}'\n"
                f"Error Details: {error_details}"
            ) from e


class OSEnvAdapter(EnvAdapter):
    def __call__(self, key: str) -> Optional[int | float]:

        val = os.environ.get(key)
        if val is None:
            return None

        return parse_numeric_input(val)


class CommandRunnerWithEnvLookUp(CommandRunner):
    def __init__(self, env_adapter: EnvAdapter, command_runner: CommandRunner) -> None:
        self.env_adapter = env_adapter
        self.command_runner = command_runner

    def __call__(self, ratchet: Ratchet) -> int | float:
        slug = ratchet_to_slug(ratchet)
        env_res = self.env_adapter(slug)

        if env_res is not None:
            return env_res

        return self.command_runner(ratchet)
