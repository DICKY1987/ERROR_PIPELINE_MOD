"""JSONL log writer with deterministic rotation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable


class JSONLRotatingLogger:
    """Append-only JSONL logger with size-based rotation."""

    def __init__(self, log_path: Path, max_bytes: int = 75 * 1024) -> None:
        self.log_path = Path(log_path)
        self.max_bytes = max_bytes

    def append(self, record: Dict[str, object]) -> None:
        line = json.dumps(record, sort_keys=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self._rotate_if_needed()

    def _rotate_if_needed(self) -> None:
        if not self.log_path.exists():
            return
        if self.log_path.stat().st_size <= self.max_bytes:
            return
        lines = self.log_path.read_text("utf-8").splitlines()
        keep: Iterable[str]
        total = 0
        kept: list[str] = []
        for line in reversed(lines):
            encoded_size = len(line.encode("utf-8")) + 1
            if total + encoded_size > self.max_bytes:
                break
            kept.append(line)
            total += encoded_size
        kept.reverse()
        data = "\n".join(kept)
        if data:
            data += "\n"
        tmp_path = self.log_path.with_suffix(".tmp")
        tmp_path.write_text(data, encoding="utf-8")
        os.replace(tmp_path, self.log_path)


__all__ = ["JSONLRotatingLogger"]
