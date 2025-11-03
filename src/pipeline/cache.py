"""Hash-based incremental validation cache."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict


@dataclass
class CacheEntry:
    hash: str
    last_validated: str
    had_errors: bool = False


class FileHashCache:
    """Persisted hash cache that tracks file validation state."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = Path(cache_path)
        self._data: Dict[str, CacheEntry] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        if not self.cache_path.exists():
            return
        try:
            raw = json.loads(self.cache_path.read_text("utf-8"))
        except json.JSONDecodeError:
            raw = {}
        for key, value in raw.items():
            self._data[key] = CacheEntry(**value)

    def _serialize(self) -> Dict[str, Dict[str, object]]:
        return {
            key: {
                "hash": entry.hash,
                "last_validated": entry.last_validated,
                "had_errors": entry.had_errors,
            }
            for key, entry in self._data.items()
        }

    def has_changed(self, file_path: Path) -> bool:
        file_path = Path(file_path).resolve()
        file_key = str(file_path)
        digest = sha256(file_path.read_bytes()).hexdigest()
        entry = self._data.get(file_key)
        if entry is None or entry.hash != digest:
            self._data[file_key] = CacheEntry(
                hash=digest,
                last_validated=self._now(),
                had_errors=False,
            )
            self._dirty = True
            return True
        return False

    def mark_validated(self, file_path: Path, had_errors: bool) -> None:
        file_key = str(Path(file_path).resolve())
        entry = self._data.setdefault(
            file_key,
            CacheEntry(hash="", last_validated=self._now(), had_errors=had_errors),
        )
        entry.last_validated = self._now()
        entry.had_errors = had_errors
        self._dirty = True

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def save(self) -> None:
        if not self._dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.cache_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(self._serialize(), indent=2), encoding="utf-8")
        os.replace(tmp_path, self.cache_path)
        self._dirty = False

    def __enter__(self) -> "FileHashCache":
        return self

    def __exit__(self, *exc_info) -> None:
        self.save()


__all__ = ["CacheEntry", "FileHashCache"]
