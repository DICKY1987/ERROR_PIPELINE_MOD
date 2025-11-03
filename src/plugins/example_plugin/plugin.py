"""Example plugin used to validate plugin discovery."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Sequence

from src.plugins.base_plugin import BasePlugin, PluginExecutionError


class ExamplePlugin(BasePlugin):
    """A minimal plugin that echoes the processed file path."""

    def check_tool_available(self) -> bool:
        # The plugin relies solely on the Python interpreter, which is assumed available.
        return True

    def build_command(self, target: Path) -> Sequence[str]:
        script = (
            "import json, pathlib, sys; "
            "print(json.dumps({'target': pathlib.Path(sys.argv[1]).name}))"
        )
        return ["python", "-c", script, str(target)]

    def parse_output(self, completed: subprocess.CompletedProcess[str]) -> Dict[str, Any]:
        if completed.returncode != 0:
            raise PluginExecutionError(
                f"Example plugin failed with code {completed.returncode}: {completed.stderr.strip()}"
            )

        try:
            payload = json.loads(completed.stdout.strip())
        except json.JSONDecodeError as exc:
            raise PluginExecutionError(
                f"Example plugin produced invalid JSON output: {exc}"
            ) from exc

        return {
            "result": payload,
            "stderr": completed.stderr.strip(),
            "returncode": completed.returncode,
        }

    def run(self, target: Path) -> Dict[str, Any]:
        """Convenience helper used during manual testing."""

        command = self.build_command(target)
        completed = self.run_subprocess(command, cwd=self.plugin_dir)
        return self.parse_output(completed)
