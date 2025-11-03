"""Command line interface for the validation pipeline."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Iterable, List

from .pipeline.cache import FileHashCache
from .pipeline.engine import PipelineEngine
from .pipeline.jsonl import JSONLRotatingLogger
from .pipeline.plugins import BasePlugin, PluginManager


def _load_plugin(spec: str) -> BasePlugin:
    if ":" not in spec:
        raise ValueError("Plugin specification must be in 'module:ClassName' format")
    module_name, class_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    try:
        plugin_cls = getattr(module, class_name)
    except AttributeError as exc:
        raise ValueError(f"Plugin class '{class_name}' not found in module '{module_name}'") from exc
    plugin = plugin_cls()  # type: ignore[call-arg]
    if not isinstance(plugin, BasePlugin):
        raise TypeError(f"Plugin '{plugin_cls}' must inherit from BasePlugin")
    return plugin


def build_engine(plugins: Iterable[BasePlugin], cache_path: Path, log_path: Path) -> PipelineEngine:
    manager = PluginManager(list(plugins))
    cache = FileHashCache(cache_path)
    logger = JSONLRotatingLogger(log_path)
    return PipelineEngine(manager, cache, logger)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic validation pipeline")
    parser.add_argument("inputs", nargs="+", help="Input files to validate")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--plugin",
        action="append",
        dest="plugins",
        required=True,
        help="Plugin specification in module:Class format. Can be provided multiple times.",
    )
    parser.add_argument("--cache", default=".pipeline_cache.json")
    parser.add_argument("--log", default="pipeline_errors.jsonl")

    args = parser.parse_args(argv)
    plugins = [_load_plugin(spec) for spec in args.plugins]
    engine = build_engine(plugins, Path(args.cache), Path(args.log))
    results = engine.process_files([Path(p) for p in args.inputs], Path(args.output))
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
