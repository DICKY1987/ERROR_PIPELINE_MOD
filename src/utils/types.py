"""Shared type stubs consumed across the provisional code base."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class ValidationError:
    """Represents a single issue reported by a plugin."""

    tool: str
    severity: str
    message: str
    file: Optional[Path] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None
    auto_fixed: Optional[bool] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginResult:
    """Container returned by plugins after execution."""

    plugin_id: str
    name: str
    success: bool
    duration_s: Optional[float] = None
    auto_fixed: int = 0
    errors: List[ValidationError] = field(default_factory=list)
    raw_output: Optional[str] = None


@dataclass
class PipelineReport:
    """Summary returned to the GUI layer for each processed file."""

    file_in: Path
    file_out: Optional[Path]
    run_id: str
    plugin_results: Sequence[PluginResult]
    summary: Dict[str, Any]


PluginManifest = Dict[str, Any]

__all__ = [
    "ValidationError",
    "PluginResult",
    "PipelineReport",
    "PluginManifest",
]
