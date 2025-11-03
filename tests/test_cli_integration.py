"""Integration tests that exercise the CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.cli as cli
from src.pipeline.cache import FileHashCache
from src.pipeline.engine import PipelineEngine
from src.pipeline.jsonl import JSONLRotatingLogger
from src.pipeline.plugins import PluginManager

from .dummy_plugins import AnalysisPlugin, HeaderPlugin


def test_cli_runs_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    input_file = tmp_path / "sample.txt"
    input_file.write_text("first line\n\nsecond line\n", encoding="utf-8")
    output_dir = tmp_path / "out"
    cache_path = tmp_path / "cache.json"
    log_path = tmp_path / "events.jsonl"

    def _build_engine(plugins, cache_path, log_path):
        manager = PluginManager(list(plugins))
        return PipelineEngine(
            manager,
            FileHashCache(cache_path),
            JSONLRotatingLogger(log_path),
            run_id_factory=lambda: "CLI-RUN",
            clock=lambda: "2025-01-01T00:00:00Z",
        )

    monkeypatch.setattr(cli, "build_engine", _build_engine)

    exit_code = cli.main(
        [
            str(input_file),
            "--output",
            str(output_dir),
            "--plugin",
            "tests.dummy_plugins:HeaderPlugin",
            "--plugin",
            "tests.dummy_plugins:AnalysisPlugin",
            "--cache",
            str(cache_path),
            "--log",
            str(log_path),
        ]
    )
    assert exit_code == 0

    captured = capsys.readouterr().out
    result = json.loads(captured)
    assert result[0]["summary"]["plugins_run"] == 2
    assert result[0]["plugins"][0]["plugin_id"] == "header"
    assert Path(result[0]["file_out"]).name.endswith("_VALIDATED.txt")
