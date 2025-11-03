"""Persistent SHA-256 cache used for incremental validation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents the cached state of a validated file."""

    hash: str
    last_validated: str
    had_errors: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "hash": self.hash,
            "last_validated": self.last_validated,
            "had_errors": self.had_errors,
        }


class FileHashCache:
    """Track file hashes and validation metadata on disk.

    The cache stores entries keyed by the absolute path of the validated file.
    Each entry records the last known SHA-256 digest, the timestamp of the
    validation, and whether the previous run produced any errors. The class is
    designed to be side-effect free until :meth:`save` is invoked, making it
    safe to use in long-running applications where writes should be batched.
    """

    def __init__(self, cache_file: Path):
        self.cache_file = Path(cache_file)
        self._cache: Dict[str, CacheEntry] = {}
        self._pending_hashes: Dict[str, str] = {}
        self._dirty = False
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def has_changed(self, file_path: Path) -> bool:
        """Return ``True`` when the file content differs from the cache.

        The method computes the current SHA-256 digest and compares it with the
        cached value. The computed hash is staged so that follow-up calls to
        :meth:`mark_validated` do not need to hash the same file again.
        """

        file_path = Path(file_path).resolve()
        if not file_path.is_file():  # pragma: no cover - guard rail
            raise FileNotFoundError(file_path)

        file_key = str(file_path)
        current_hash = self._hash_file(file_path)
        self._pending_hashes[file_key] = current_hash

        entry = self._cache.get(file_key)
        if entry is None:
            return True
        return entry.hash != current_hash

    def mark_validated(self, file_path: Path, had_errors: bool) -> None:
        """Update (or create) the cache entry after validation."""

        file_path = Path(file_path).resolve()
        file_key = str(file_path)
        file_hash = self._pending_hashes.pop(file_key, None)
        if file_hash is None:
            file_hash = self._hash_file(file_path)

        timestamp = datetime.now(timezone.utc).isoformat()
        self._cache[file_key] = CacheEntry(
            hash=file_hash,
            last_validated=timestamp,
            had_errors=bool(had_errors),
        )
        self._dirty = True

    def get_entry(self, file_path: Path) -> Optional[CacheEntry]:
        """Return the cached entry for ``file_path`` if available."""

        return self._cache.get(str(Path(file_path).resolve()))

    def remove(self, file_path: Path) -> None:
        """Remove the cached entry for a file, if it exists."""

        file_key = str(Path(file_path).resolve())
        if file_key in self._cache:
            del self._cache[file_key]
            self._dirty = True

    def save(self) -> None:
        """Persist the cache to disk using an atomic write."""

        if not self._dirty:
            return

        data = {path: entry.to_dict() for path, entry in self._cache.items()}
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=self.cache_file.parent,
            prefix=".tmp_cache_",
            suffix=self.cache_file.suffix or ".json",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.cache_file)
            self._dirty = False
        except Exception:  # pragma: no cover - defensive cleanup
            LOGGER.exception("Failed to save hash cache to %s", self.cache_file)
            raise
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    LOGGER.debug("Unable to remove temp cache file: %s", tmp_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.cache_file.exists():
            return

        try:
            raw = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Cache file %s is corrupted; starting fresh", self.cache_file)
            return
        except OSError as exc:  # pragma: no cover - disk failure
            LOGGER.warning("Unable to read cache file %s: %s", self.cache_file, exc)
            return

        for path, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            hash_value = payload.get("hash")
            last_validated = payload.get("last_validated")
            had_errors = payload.get("had_errors", False)
            if not isinstance(hash_value, str) or not isinstance(last_validated, str):
                continue
            self._cache[path] = CacheEntry(
                hash=hash_value,
                last_validated=last_validated,
                had_errors=bool(had_errors),
            )

    @staticmethod
    def _hash_file(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

