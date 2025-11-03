"""Unit tests for JSONL rotation behaviour."""

from __future__ import annotations

import json
from pathlib import Path

from src.pipeline.jsonl import JSONLRotatingLogger


def test_jsonl_rotation_keeps_recent_entries(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    logger = JSONLRotatingLogger(log_path, max_bytes=120)

    for idx in range(10):
        logger.append({"index": idx, "message": f"event-{idx}"})

    content = log_path.read_text("utf-8").strip().splitlines()
    records = [json.loads(line) for line in content]
    assert records[0]["index"] > 0
    assert records[-1]["index"] == 9
    encoded_size = sum(len(line.encode("utf-8")) + 1 for line in log_path.read_text("utf-8").splitlines())
    assert encoded_size <= 120
