"""Unit tests for FileHashCache behaviour."""

from __future__ import annotations

from pathlib import Path

from src.pipeline.cache import FileHashCache


def test_cache_detects_changes(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    target = tmp_path / "example.txt"
    target.write_text("alpha", encoding="utf-8")

    cache = FileHashCache(cache_file)
    assert cache.has_changed(target) is True
    cache.save()
    assert cache.has_changed(target) is False

    target.write_text("beta", encoding="utf-8")
    assert cache.has_changed(target) is True

    cache.mark_validated(target, had_errors=True)
    cache.save()
    reloaded = FileHashCache(cache_file)
    assert reloaded.has_changed(target) is False
    assert reloaded._data[str(target.resolve())].had_errors is True
