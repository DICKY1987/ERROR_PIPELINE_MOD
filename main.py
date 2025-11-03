"""Application entry point for the validation pipeline GUI."""
from __future__ import annotations

import tkinter as tk

try:  # pragma: no cover - optional drag-and-drop support
    from tkinterdnd2 import TkinterDnD
except Exception:  # pragma: no cover
    TkinterDnD = None

from src.core.pipeline_engine import PipelineEngine
from src.gui.main_window import ValidationPipelineGUI


def _create_root() -> tk.Tk:
    if TkinterDnD is not None:
        return TkinterDnD.Tk()
    return tk.Tk()


def main() -> None:
    """Launch the GUI application."""
    pipeline_engine = PipelineEngine()
    root = _create_root()
    app = ValidationPipelineGUI(root, pipeline_engine)
    app.run()


if __name__ == "__main__":
    main()
