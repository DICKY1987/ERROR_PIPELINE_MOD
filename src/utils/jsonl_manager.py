"""Utility for writing JSONL files with automatic size-based rotation."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

DEFAULT_MAX_BYTES = 75 * 1024


class JSONLManager:
    """Append-only JSONL writer with atomic rotation semantics."""

    def __init__(self, path: Path, *, max_bytes: int = DEFAULT_MAX_BYTES):
        self.path = Path(path)
        self.max_bytes = max_bytes
        self._lock = Lock()

    # ------------------------------------------------------------------
    def append(self, record: Any) -> None:
        """Append a record to the JSONL file and rotate if it exceeds the limit."""

        line = json.dumps(record, ensure_ascii=False)
        data = f"{line}\n"

        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(data)
            self._rotate_if_needed()

    # ------------------------------------------------------------------
    def _rotate_if_needed(self) -> None:
        if not self.path.exists():
            return

        size = self.path.stat().st_size
        if size <= self.max_bytes:
            return

        keep_lines = list(self._tail_lines())

        fd, tmp_path = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".tmp_jsonl_",
            suffix=self.path.suffix or ".jsonl",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for line in keep_lines:
                    handle.write(f"{line}\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _tail_lines(self) -> Iterable[str]:
        """Yield the newest lines that fit within ``self.max_bytes``."""

        with self.path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            end = handle.tell()
            if end <= self.max_bytes:
                handle.seek(0)
                data = handle.read().decode("utf-8")
                for line in data.splitlines():
                    yield line
                return

            buffer = bytearray()
            pos = end
            target = self.max_bytes * 2
            while pos > 0 and len(buffer) < target:
                step = min(8192, pos)
                pos -= step
                handle.seek(pos)
                chunk = handle.read(step)
                buffer[:0] = chunk

            data = bytes(buffer)
            if pos > 0:
                newline_index = data.find(b"\n")
                if newline_index != -1:
                    data = data[newline_index + 1 :]
                else:
                    data = b""

        text = data.decode("utf-8", errors="ignore")
        lines = text.splitlines()
        total = 0
        kept = []
        for line in reversed(lines):
            encoded = line.encode("utf-8")
            line_size = len(encoded) + 1
            if total + line_size > self.max_bytes:
                break
            kept.append(line)
            total += line_size
        return reversed(kept)

