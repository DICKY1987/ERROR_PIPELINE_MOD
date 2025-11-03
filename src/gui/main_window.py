"""Tkinter GUI for the validation pipeline."""
from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Iterable, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

try:  # pragma: no cover - optional dependency for drag and drop
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - library may be unavailable in tests
    TkinterDnD = None
    DND_FILES = "DND_Files"


class ValidationPipelineGUI:
    """Main window for interacting with the validation pipeline."""

    MAX_FILES = 10

    def __init__(self, root: tk.Tk, pipeline_engine) -> None:
        self.root = root
        self.pipeline_engine = pipeline_engine

        self.files: List[Path] = []
        self.processing_thread: Optional[threading.Thread] = None
        self.ui_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()

        self.output_dir = Path.cwd()

        self._configure_root()
        self._build_widgets()
        self._register_events()

        self.root.after(100, self._drain_ui_queue)

    # ------------------------------------------------------------------
    # Tk setup helpers
    def _configure_root(self) -> None:
        self.root.title("Validation Pipeline")
        self.root.geometry("720x520")
        self.root.minsize(640, 480)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _build_widgets(self) -> None:
        self.mainframe = ttk.Frame(self.root, padding=12)
        self.mainframe.grid(sticky="nsew")
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(3, weight=1)

        # File drop area -------------------------------------------------
        drop_frame = ttk.LabelFrame(self.mainframe, text="Files")
        drop_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=(0, 10))
        drop_frame.columnconfigure(0, weight=1)
        drop_frame.rowconfigure(1, weight=1)

        instruction = ttk.Label(
            drop_frame,
            text="Drag and drop up to 10 files below or use the buttons to add them.",
            justify="center",
        )
        instruction.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(4, 6))

        self.file_listbox = tk.Listbox(
            drop_frame,
            height=8,
            selectmode=tk.EXTENDED,
            activestyle="dotbox",
        )
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=(0, 6))

        button_frame = ttk.Frame(drop_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.add_button = ttk.Button(button_frame, text="Add Files…", command=self._open_file_dialog)
        self.add_button.grid(row=0, column=0, sticky="ew", padx=2)

        self.remove_button = ttk.Button(button_frame, text="Remove Selected", command=self._remove_selected)
        self.remove_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self._clear_files)
        self.clear_button.grid(row=0, column=2, sticky="ew", padx=2)

        # Output directory selection ------------------------------------
        output_frame = ttk.LabelFrame(self.mainframe, text="Output")
        output_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)

        self.output_var = tk.StringVar(value=str(self.output_dir))
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(6, 4), pady=8)

        self.browse_button = ttk.Button(output_frame, text="Browse…", command=self._choose_output_folder)
        self.browse_button.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=8)

        # Process button -------------------------------------------------
        action_frame = ttk.Frame(self.mainframe)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        action_frame.columnconfigure(0, weight=1)
        self.process_button = ttk.Button(action_frame, text="Process Files", command=self._start_processing)
        self.process_button.grid(row=0, column=0, sticky="ew")

        # Log area -------------------------------------------------------
        log_frame = ttk.LabelFrame(self.mainframe, text="Log")
        log_frame.grid(row=3, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_widget = scrolledtext.ScrolledText(log_frame, state="disabled", wrap=tk.WORD, height=10)
        self.log_widget.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Status bar -----------------------------------------------------
        status_frame = ttk.Frame(self.mainframe)
        status_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w")

    def _register_events(self) -> None:
        if TkinterDnD and hasattr(self.file_listbox, "drop_target_register"):
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind("<<Drop>>", self._on_drop)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # File management helpers
    def _open_file_dialog(self) -> None:
        initial_dir = str(Path.cwd())
        filenames = filedialog.askopenfilenames(parent=self.root, title="Select files", initialdir=initial_dir)
        if filenames:
            self._add_files(filenames)

    def _on_drop(self, event) -> None:  # type: ignore[override]
        data: Iterable[str] = self.root.tk.splitlist(event.data)
        self._add_files(data)

    def _add_files(self, file_paths: Iterable[str]) -> None:
        added = 0
        for path_str in file_paths:
            path = Path(path_str).expanduser()
            if not path.exists() or not path.is_file():
                self._append_log(f"Ignoring non-file path: {path}")
                continue
            if path in self.files:
                continue
            if len(self.files) >= self.MAX_FILES:
                messagebox.showwarning("Limit reached", f"Only {self.MAX_FILES} files can be processed at a time.")
                break
            self.files.append(path)
            self.file_listbox.insert(tk.END, str(path))
            added += 1
        if added:
            self.status_var.set(f"{len(self.files)} file(s) queued.")

    def _remove_selected(self) -> None:
        selected = list(self.file_listbox.curselection())
        if not selected:
            return
        for index in reversed(selected):
            try:
                self.files.pop(index)
            except IndexError:
                continue
            self.file_listbox.delete(index)
        self.status_var.set(f"{len(self.files)} file(s) queued.")

    def _clear_files(self) -> None:
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.status_var.set("Ready.")

    # ------------------------------------------------------------------
    # Output folder selection
    def _choose_output_folder(self) -> None:
        directory = filedialog.askdirectory(parent=self.root, title="Select output folder", initialdir=str(self.output_dir))
        if directory:
            self.output_dir = Path(directory)
            self.output_var.set(str(self.output_dir))

    # ------------------------------------------------------------------
    # Processing logic
    def _start_processing(self) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            return
        if not self.files:
            messagebox.showinfo("No files", "Add at least one file to process.")
            return

        output_dir = Path(self.output_var.get()).expanduser()
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:  # pragma: no cover - depends on filesystem
                messagebox.showerror("Output folder", f"Could not create output folder:\n{exc}")
                return

        self._set_processing_state(True)
        self._append_log(f"Starting processing of {len(self.files)} file(s)…")

        files_snapshot = list(self.files)
        self.processing_thread = threading.Thread(
            target=self._run_pipeline,
            args=(files_snapshot, output_dir),
            daemon=True,
        )
        self.processing_thread.start()

    def _run_pipeline(self, files: List[Path], output_dir: Path) -> None:
        try:
            results = self.pipeline_engine.process_files(files, output_dir, progress_callback=self._queue_progress)
            self.ui_queue.put(("processing-done", results))
        except Exception as exc:  # pragma: no cover - defensive
            self.ui_queue.put(("processing-error", exc))

    def _queue_progress(self, file_path: Path, result) -> None:
        message = f"Processed {file_path.name}: {result.get('status', 'done')}"
        self.ui_queue.put(("log", message))

    def _set_processing_state(self, running: bool) -> None:
        if running:
            self.process_button.state(["disabled"])
            self.status_var.set("Processing…")
        else:
            self.process_button.state(["!disabled"])
            self.status_var.set("Ready.")

    # ------------------------------------------------------------------
    # UI queue management
    def _drain_ui_queue(self) -> None:
        try:
            while True:
                message_type, payload = self.ui_queue.get_nowait()
                if message_type == "log":
                    self._append_log(str(payload))
                elif message_type == "processing-done":
                    self._on_processing_done(payload)
                elif message_type == "processing-error":
                    self._on_processing_error(payload)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._drain_ui_queue)

    def _on_processing_done(self, results) -> None:
        success = sum(1 for r in results if r.get("status") not in {"failed", "missing", "error"})
        total = len(results)
        self._append_log(f"Processing complete: {success}/{total} succeeded.")
        self._set_processing_state(False)

    def _on_processing_error(self, exc: Exception) -> None:
        self._append_log(f"Error: {exc}")
        messagebox.showerror("Processing error", str(exc))
        self._set_processing_state(False)

    # ------------------------------------------------------------------
    # Utilities
    def _append_log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state="disabled")

    def _on_close(self) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            if not messagebox.askyesno("Quit", "Processing is running. Quit anyway?"):
                return
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
