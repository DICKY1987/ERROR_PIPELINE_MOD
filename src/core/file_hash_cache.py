"""Incremental validation cache placeholder."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional


class FileHashCache:
    """Stores hashes of previously validated files for incremental runs."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.cache: Dict[str, Dict[str, object]] = {}

    def load(self) -> None:
        """Load the cache data from disk."""
        raise NotImplementedError("Cache loading is not implemented")

    def save(self) -> None:
        """Persist the cache data to disk."""
        raise NotImplementedError("Cache saving is not implemented")

    def has_changed(self, file_path: Path) -> bool:
        """Return ``True`` when the file content differs from the cached entry."""
        raise NotImplementedError("Change detection is not implemented")

    def mark_validated(self, file_path: Path, had_errors: Optional[bool] = None) -> None:
        """Update the cache record for a file after successful validation."""
        raise NotImplementedError("Cache update is not implemented")
