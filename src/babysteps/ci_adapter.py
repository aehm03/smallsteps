import re
from pathlib import Path
from typing import List

from babysteps.ratchet import Ratchet


def ratchet_to_slug(ratchet: Ratchet) -> str:
    """Generates a standardized environment variable key for a given ratchet name."""
    return f"BABYSTEPS_{re.sub(r'[^a-zA-Z0-9]', '_', ratchet.name).upper()}"


class GitHubCIAdapter:
    """Generates a custom local GitHub Composite Action matched to the project metrics."""

    def generate_action(self, ratchets: List[Ratchet]) -> str:
        """Generates an action.yml manifest string with dynamic inputs, setup stubs, and mapping."""
        yaml_lines = [
            "name: 'Babysteps Ratchet Evaluation'",
            "description: 'Evaluates your quality goals'",
        ]

        # 1. Append inputs only if there are active ratchets to list
        if ratchets:
            yaml_lines.append("inputs:")
            for r in ratchets:
                slug = ratchet_to_slug(r)
                yaml_lines.extend(
                    [
                        f"  {slug}:",
                        f"    description: \"Current live performance value for '{r.name}'\"",
                        "    required: true",
                    ]
                )

        # 2. Append core composite block infrastructure and the installation placeholder
        yaml_lines.extend(
            [
                "",
                "runs:",
                "  using: 'composite'",
                "  steps:",
                "    - name: Install uv",
                "      uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0",
                "      with:",
                "        enable-cache: true",
                "",
                "    - name: Run BabySteps Guardrail Validation",
                "      shell: bash",
                "      run: uvx babysteps-ratchet check",
            ]
        )

        # 3. Append step context environment maps sequentially via loop execution
        if ratchets:
            yaml_lines.append("      env:")
            for r in ratchets:
                slug = ratchet_to_slug(r)
                yaml_lines.append(f"        {slug}: ${{{{ inputs.{slug} }}}}")

        return "\n".join(yaml_lines) + "\n"

    def save(self, path: Path, content: str) -> None:
        """Writes the custom composite action metadata safely out to file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise IOError(f"Failed to write local custom action configuration: {e}")
