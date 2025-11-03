"""Minimal pipeline engine for the validation GUI."""
from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Callable, Iterable, List, Dict, Any, Optional


ProgressCallback = Callable[[Path, Dict[str, Any]], None]


class PipelineEngine:
    """A minimal stand-in for the validation pipeline engine.

    The real implementation would perform plugin-based validation and report
    results for each processed file.  This lightweight version focuses on the
    interface expected by the GUI so that user interactions can be exercised
    without the full validation stack.
    """

    def __init__(self) -> None:
        self._lock = Lock()

    def process_files(
        self,
        file_paths: Iterable[Path],
        output_dir: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[Dict[str, Any]]:
        """Process the provided files.

        Args:
            file_paths: Iterable of file paths to process.
            output_dir: Directory where validated files would normally be
                written.  The directory is created if it does not exist.
            progress_callback: Optional callback invoked after each file with
                the file path and result dictionary.

        Returns:
            A list of dictionaries describing the outcome for each file.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: List[Dict[str, Any]] = []
        for raw_path in file_paths:
            file_path = Path(raw_path)
            with self._lock:
                result = self._process_single_file(file_path, output_dir)

            if progress_callback is not None:
                progress_callback(file_path, result)

            results.append(result)
        return results

    def _process_single_file(self, file_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Fake processing for a single file.

        The implementation simply checks if the file exists.  In a real engine
        this method would coordinate plugin execution, copy outputs, and
        generate detailed reports.
        """

        status: str
        message: str
        if file_path.exists() and file_path.is_file():
            status = "processed"
            message = "File processed (placeholder)."
        else:
            status = "missing"
            message = "File not found; skipped processing."

        return {
            "file": str(file_path),
            "status": status,
            "message": message,
            "output_dir": str(output_dir),
        }
