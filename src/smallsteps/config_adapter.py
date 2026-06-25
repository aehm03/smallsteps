import tomllib
from datetime import date
from pathlib import Path
from typing import List

from pydantic import TypeAdapter

from smallsteps.ratchet import Ratchet


class TOMLConfigAdapter:
    """Manages reading, validating, and mutating the smallsteps TOML file structure."""

    def load(self, path: Path) -> List[Ratchet]:
        """Reads and parses the entire configuration file into a list of valid Ratchets."""
        if not path.exists():
            return []

        try:
            with open(path, "rb") as f:
                toml_data = tomllib.load(f)

            return TypeAdapter(List[Ratchet]).validate_python(
                toml_data.get("ratchets", [])
            )
        except Exception as e:
            raise RuntimeError(
                f"Malformed or invalid configuration at {path.name}:\n{e}"
            )

    def append(self, path: Path, ratchet: Ratchet) -> None:
        """Serializes a single valid Ratchet and appends it structurally to the file."""
        # Auto-initialize the file if it doesn't exist yet
        #
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Smallsteps Configuration\n", encoding="utf-8")

        toml_lines = ["", "[[ratchets]]"]
        for key, value in ratchet.model_dump().items():
            if isinstance(value, date):
                toml_lines.append(f"{key} = {value.isoformat()}")
            elif isinstance(value, str):
                toml_lines.append(f'{key} = "{value}"')
            else:
                toml_lines.append(f"{key} = {value}")

        toml_block = "\n".join(toml_lines) + "\n"

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(toml_block)
        except Exception as e:
            raise IOError(f"Failed to write ratchet data to filesystem: {e}")
