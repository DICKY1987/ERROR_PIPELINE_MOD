"""Base class and utilities for validation pipeline plugins."""
from __future__ import annotations

import json
import shlex
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence


class PluginError(RuntimeError):
    """Base exception type for plugin related failures."""


class ManifestError(PluginError):
    """Raised when a plugin manifest is invalid."""


class PluginExecutionError(PluginError):
    """Raised when execution of a plugin command fails."""


class BasePlugin(ABC):
    """Base class for all validation pipeline plugins."""

    def __init__(self, manifest: Mapping[str, Any], plugin_dir: Path) -> None:
        self._manifest: Mapping[str, Any] = manifest
        self._plugin_dir = plugin_dir

    @property
    def name(self) -> str:
        name = self._manifest.get("name")
        if not isinstance(name, str):  # pragma: no cover - defensive branch
            raise ManifestError("Plugin manifest missing required 'name' field")
        return name

    @property
    def manifest(self) -> Mapping[str, Any]:
        return self._manifest

    @property
    def plugin_dir(self) -> Path:
        return self._plugin_dir

    @abstractmethod
    def build_command(self, target: Path) -> Sequence[str]:
        """Return the command to execute for the provided target path."""

    @abstractmethod
    def parse_output(self, completed: subprocess.CompletedProcess[str]) -> Any:
        """Convert a completed process into the plugin's domain output."""

    @abstractmethod
    def check_tool_available(self) -> bool:
        """Return whether the external tool required by the plugin is available."""

    @staticmethod
    def load_manifest(path: Path) -> Dict[str, Any]:
        """Load and validate a plugin manifest from JSON."""

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ManifestError(f"Manifest not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ManifestError(f"Invalid JSON in manifest {path}: {exc}") from exc

        if not isinstance(data, MutableMapping):
            raise ManifestError("Plugin manifest must decode to a JSON object")

        if "name" not in data:
            raise ManifestError("Plugin manifest missing required 'name'")

        dependencies = data.get("dependencies", [])
        if dependencies and not isinstance(dependencies, list):
            raise ManifestError("'dependencies' must be a list when provided")

        return dict(data)

    @staticmethod
    def run_subprocess(
        command: Sequence[str] | str,
        *,
        cwd: Optional[Path] = None,
        timeout: Optional[float] = None,
        env: Optional[Mapping[str, str]] = None,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Run a subprocess safely and capture its output."""

        if isinstance(command, str):
            command = shlex.split(command)

        if not command:
            raise PluginExecutionError("Command must contain at least one token")

        try:
            completed = subprocess.run(  # noqa: S603,S607 - trusted command construction
                command,
                cwd=str(cwd) if cwd else None,
                env=dict(env) if env is not None else None,
                timeout=timeout,
                check=check,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PluginExecutionError(str(exc)) from exc

        return completed
