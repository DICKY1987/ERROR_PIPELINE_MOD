"""Common plugin interfaces used by the validation pipeline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import time


@dataclass
class ValidationError:
    """Structured representation of a validation error or warning."""

    tool: str
    severity: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None
    auto_fixed: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the error to a JSON-compatible dictionary."""

        data = {
            "tool": self.tool,
            "severity": self.severity,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "auto_fixed": self.auto_fixed,
        }
        if self.extra:
            data["extra"] = self.extra
        return data


@dataclass
class PluginResult:
    """Result returned by a plugin execution."""

    plugin_id: str
    name: str
    success: bool
    duration_s: float
    auto_fixed_count: int
    errors: List[ValidationError] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the plugin result to a dictionary."""

        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "success": self.success,
            "duration_s": self.duration_s,
            "auto_fixed": self.auto_fixed_count,
            "errors": [error.to_dict() for error in self.errors],
            "details": self.details,
        }


class BasePlugin(ABC):
    """Base class used by the pipeline engine to interact with plugins."""

    plugin_id: str
    name: str
    manifest: Dict[str, Any]
    enabled: bool

    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
        self.plugin_id = manifest.get("plugin_id", self.__class__.__name__)
        self.name = manifest.get("name", self.plugin_id)
        self.enabled = manifest.get("enabled", True)

    @property
    def requires(self) -> Iterable[str]:
        """Return the plugin identifiers that must run before this plugin."""

        return self.manifest.get("requires", [])

    @property
    def file_extensions(self) -> Iterable[str]:
        """Return file extensions supported by this plugin."""

        return [ext.lower() for ext in self.manifest.get("file_extensions", [])]

    def can_process(self, file_path: Path) -> bool:
        """Determine whether the plugin can process the supplied file."""

        if not self.enabled:
            return False
        extensions = list(self.file_extensions)
        return not extensions or file_path.suffix.lower() in extensions

    def execute(self, file_path: Path) -> PluginResult:
        """Execute the plugin while capturing failures as structured results."""

        start = time.perf_counter()
        try:
            result = self.run(file_path)
        except Exception as exc:  # pragma: no cover - defensive
            duration = time.perf_counter() - start
            error = ValidationError(
                tool=self.name,
                severity="error",
                message=str(exc),
                file=str(file_path),
            )
            return PluginResult(
                plugin_id=self.plugin_id,
                name=self.name,
                success=False,
                duration_s=duration,
                auto_fixed_count=0,
                errors=[error],
            )

        duration = time.perf_counter() - start
        if result.duration_s <= 0:
            result.duration_s = duration
        return result

    @abstractmethod
    def run(self, file_path: Path) -> PluginResult:
        """Execute the plugin and return a :class:`PluginResult`."""

