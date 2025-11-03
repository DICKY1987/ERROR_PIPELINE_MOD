"""Integration tests for the pipeline engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from src.pipeline.cache import FileHashCache
from src.pipeline.engine import PipelineEngine
from src.pipeline.jsonl import JSONLRotatingLogger
from src.pipeline.plugins import PluginManager

from .dummy_plugins import AnalysisPlugin, HeaderPlugin


def _clock_factory(values: Iterator[str]):
    values = iter(values)

    def _next() -> str:
        try:
            return next(values)
        except StopIteration:
            return "1970-01-01T00:00:00Z"

    return _next


def test_pipeline_produces_golden_report(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.txt"
    input_file.write_text("first line\n\nsecond line\n", encoding="utf-8")
    output_dir = tmp_path / "out"
    cache_path = tmp_path / "cache.json"
    log_path = tmp_path / "events.jsonl"

    manager = PluginManager([HeaderPlugin(), AnalysisPlugin()])
    engine = PipelineEngine(
        plugin_manager=manager,
        cache=FileHashCache(cache_path),
        jsonl_logger=JSONLRotatingLogger(log_path),
        run_id_factory=lambda: "RUN-001",
        clock=_clock_factory(["2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z"]),
    )

    report = engine.process_file(input_file, output_dir)

    normalized = {
        "run_id": report["run_id"],
        "timestamp": report["timestamp"],
        "file_in": Path(report["file_in"]).name,
        "file_out": Path(report["file_out"]).name,
        "status": report["status"],
        "summary": report["summary"],
        "plugins": report["plugins"],
    }
    golden_path = Path(__file__).parent / "golden" / "pipeline_report.json"
    expected = json.loads(golden_path.read_text("utf-8"))
    assert normalized == expected

    log_entries = [json.loads(line) for line in log_path.read_text("utf-8").splitlines()]
    assert log_entries[-1]["run_id"] == "RUN-001"

    second = engine.process_file(input_file, output_dir)
    assert second["status"] == "skipped"
