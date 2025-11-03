"""Dummy plugins used in integration tests."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from src.pipeline.plugins import BasePlugin, PluginResult


class HeaderPlugin(BasePlugin):
    plugin_id = "header"
    name = "Header Writer"

    def run(self, file_path: Path, state: Dict[str, object]) -> PluginResult:
        original = file_path.read_text("utf-8")
        if not original.startswith("HEADER\n"):
            file_path.write_text("HEADER\n" + original, encoding="utf-8")
        return PluginResult(
            plugin_id=self.plugin_id,
            produced=file_path,
            errors=[],
            metadata={"added_header": True},
        )


class AnalysisPlugin(BasePlugin):
    plugin_id = "analysis"
    name = "Line Analyzer"
    requires = ("header",)

    def run(self, file_path: Path, state: Dict[str, object]) -> PluginResult:
        content = file_path.read_text("utf-8")
        lines = content.splitlines()
        errors = []
        if any(len(line.strip()) == 0 for line in lines):
            errors.append(
                {
                    "severity": "warning",
                    "message": "blank line detected",
                }
            )
        metadata = {"line_count": len(lines)}
        return PluginResult(
            plugin_id=self.plugin_id,
            produced=file_path,
            errors=errors,
            metadata=metadata,
        )


__all__ = ["HeaderPlugin", "AnalysisPlugin"]
