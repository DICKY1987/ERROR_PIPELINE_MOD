"""Core pipeline orchestration for the validation system."""
from __future__ import annotations

import json
import logging
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Protocol

from .file_hash_cache import FileHashCache
from ..plugins.base_plugin import BasePlugin, PluginResult
from ..utils.jsonl_manager import JSONLManager

LOGGER = logging.getLogger(__name__)


def _generate_ulid(timestamp: Optional[datetime] = None) -> str:
    """Generate a ULID string without third-party dependencies."""

    import os

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    millis = int(timestamp.timestamp() * 1000)
    crockford32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    time_chars = []
    value = millis
    for _ in range(10):
        value, idx = divmod(value, 32)
        time_chars.append(crockford32[idx])
    time_component = "".join(reversed(time_chars)).rjust(10, "0")

    random_component = "".join(
        crockford32[b & 0x1F] for b in os.urandom(16)
    )
    return f"{time_component}{random_component}"[:26]


class PipelineEngine:
    """Coordinate plugin execution, reporting, and caching."""

    def __init__(
        self,
        plugin_manager: "PluginManagerProtocol",
        output_dir: Path,
        *,
        cache: Optional[FileHashCache] = None,
        aggregated_log: Optional[JSONLManager] = None,
    ) -> None:
        self.plugin_manager = plugin_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache = cache
        self.aggregated_log = aggregated_log or JSONLManager(
            self.output_dir / "pipeline_results.jsonl"
        )

    # ------------------------------------------------------------------
    def process_files(self, file_paths: Iterable[Path]) -> List[dict]:
        results = []
        for file_path in file_paths:
            try:
                results.append(self.process_file(Path(file_path)))
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("Failed to process file: %s", file_path)
                results.append(
                    {
                        "file": str(file_path),
                        "status": "failed",
                    }
                )
        return results

    def process_file(self, file_path: Path) -> dict:
        file_path = Path(file_path).resolve()
        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        if self.cache is not None and not self.cache.has_changed(file_path):
            LOGGER.info("Skipping %s (cache hit)", file_path.name)
            return {
                "file": str(file_path),
                "status": "skipped",
                "reason": "unchanged",
            }

        timestamp = datetime.now(timezone.utc)
        run_id = _generate_ulid(timestamp)
        plugins = self.plugin_manager.get_plugins_for_file(file_path)

        if not plugins:
            LOGGER.warning("No plugins available for %s", file_path)
            return {
                "file": str(file_path),
                "status": "no_plugins",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            working_file = Path(tmp_dir) / file_path.name
            shutil.copy2(file_path, working_file)

            plugin_summaries = []
            aggregated_entries = []
            total_errors = 0
            total_fixed = 0

            for plugin in plugins:
                if isinstance(plugin, BasePlugin) and not plugin.can_process(file_path):
                    continue
                start = time.perf_counter()
                result = plugin.execute(working_file)
                duration = time.perf_counter() - start
                if isinstance(result, PluginResult):
                    plugin_result = result
                else:  # pragma: no cover - legacy support
                    raise TypeError("Plugins must return PluginResult instances")

                if plugin_result.duration_s <= 0:
                    plugin_result.duration_s = duration

                plugin_dict = plugin_result.to_dict()
                plugin_summaries.append(plugin_dict)
                total_errors += len(plugin_result.errors)
                total_fixed += plugin_result.auto_fixed_count
                aggregated_entries.append(plugin_result)

            output_file = self._copy_to_output(file_path, working_file, timestamp, run_id)
            report = self._build_report(
                file_path=file_path,
                output_file=output_file,
                run_id=run_id,
                timestamp=timestamp,
                plugin_results=plugin_summaries,
                total_errors=total_errors,
                total_fixed=total_fixed,
            )
            self._save_json_report(output_file, report)
            self._append_aggregated_log(
                aggregated_entries, file_path, output_file, run_id, timestamp
            )

        if self.cache is not None:
            self.cache.mark_validated(file_path, had_errors=report["summary"]["total_errors"] > 0)
            self.cache.save()

        return report

    # ------------------------------------------------------------------
    def _build_report(
        self,
        *,
        file_path: Path,
        output_file: Path,
        run_id: str,
        timestamp: datetime,
        plugin_results: List[dict],
        total_errors: int,
        total_fixed: int,
    ) -> dict:
        return {
            "run_id": run_id,
            "file_in": str(file_path),
            "file_out": str(output_file),
            "timestamp_utc": timestamp.isoformat(),
            "summary": {
                "plugins_run": len(plugin_results),
                "total_errors": total_errors,
                "auto_fixed": total_fixed,
            },
            "plugin_results": plugin_results,
        }

    def _copy_to_output(
        self,
        original_file: Path,
        working_file: Path,
        timestamp: datetime,
        run_id: str,
    ) -> Path:
        suffix = original_file.suffix
        safe_timestamp = timestamp.strftime("%Y%m%d_%H%M%S")
        new_name = f"{original_file.stem}_VALIDATED_{safe_timestamp}_{run_id}{suffix}"
        destination = self.output_dir / new_name
        shutil.copy2(working_file, destination)
        return destination

    def _save_json_report(self, output_file: Path, report: dict) -> None:
        report_path = output_file.with_suffix(f"{output_file.suffix}.json")
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    def _append_aggregated_log(
        self,
        entries: Iterable[PluginResult],
        file_in: Path,
        file_out: Path,
        run_id: str,
        timestamp: datetime,
    ) -> None:
        for plugin_result in entries:
            record = {
                "run_id": run_id,
                "timestamp_utc": timestamp.isoformat(),
                "file_in": str(file_in),
                "file_out": str(file_out),
                "plugin_id": plugin_result.plugin_id,
                "plugin_name": plugin_result.name,
                "success": plugin_result.success,
                "duration_s": plugin_result.duration_s,
                "auto_fixed": plugin_result.auto_fixed_count,
                "errors": [error.to_dict() for error in plugin_result.errors],
            }
            self.aggregated_log.append(record)


class PluginManagerProtocol(Protocol):
    """Protocol describing the minimal surface used by :class:`PipelineEngine`."""

    def get_plugins_for_file(self, file_path: Path) -> Iterable[BasePlugin]:
        ...

