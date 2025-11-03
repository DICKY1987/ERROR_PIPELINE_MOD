"""High level pipeline orchestration primitives."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Dict, Iterable, List, Optional

from .cache import FileHashCache
from .jsonl import JSONLRotatingLogger
from .plugins import PluginManager, PluginResult


@dataclass
class PipelineSummary:
    plugins_run: int
    total_errors: int


class PipelineEngine:
    """Coordinates plugin execution, caching, and reporting."""

    def __init__(
        self,
        plugin_manager: PluginManager,
        cache: FileHashCache,
        jsonl_logger: JSONLRotatingLogger,
        run_id_factory: Optional[Callable[[], str]] = None,
        clock: Optional[Callable[[], str]] = None,
    ) -> None:
        self.plugin_manager = plugin_manager
        self.cache = cache
        self.jsonl_logger = jsonl_logger
        self._run_id_factory = run_id_factory or self._default_run_id
        self._clock = clock or self._default_clock

    def process_file(self, file_path: Path, output_dir: Path) -> Dict[str, object]:
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if not self.cache.has_changed(file_path):
            return {
                "run_id": self._run_id_factory(),
                "file_in": str(file_path),
                "status": "skipped",
            }

        run_id = self._run_id_factory()
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / file_path.name
            shutil.copy2(file_path, tmp_path)
            plugin_results = self.plugin_manager.execute(tmp_path)
            prepared_results: List[Dict[str, object]] = []
            total_errors = 0
            for result in plugin_results:
                prepared_results.append(
                    {
                        "plugin_id": result.plugin_id,
                        "errors": result.errors,
                        "metadata": result.metadata,
                    }
                )
                total_errors += len(result.errors)
            output_path = output_dir / f"{file_path.stem}_VALIDATED{file_path.suffix}"
            shutil.copy2(tmp_path, output_path)

        had_errors = total_errors > 0
        self.cache.mark_validated(file_path, had_errors)
        self.cache.save()
        log_record = {
            "run_id": run_id,
            "file_out": str(output_path),
            "had_errors": had_errors,
            "timestamp": self._clock(),
        }
        self.jsonl_logger.append(log_record)
        summary = PipelineSummary(
            plugins_run=len(plugin_results),
            total_errors=total_errors,
        )
        report = {
            "run_id": run_id,
            "timestamp": self._clock(),
            "file_in": str(file_path),
            "file_out": str(output_path),
            "status": "processed",
            "summary": summary.__dict__,
            "plugins": prepared_results,
        }
        return report

    def process_files(self, files: Iterable[Path], output_dir: Path) -> List[Dict[str, object]]:
        return [self.process_file(path, output_dir) for path in files]

    @staticmethod
    def _default_run_id() -> str:
        # Simplistic ULID-like placeholder: timestamp + counter fallback to uuid.
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    @staticmethod
    def _default_clock() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ["PipelineEngine", "PipelineSummary"]
