"""Minimal plugin manager with dependency-aware ordering."""
from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
import importlib.util
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..plugins.base_plugin import BasePlugin

LOGGER = logging.getLogger(__name__)


class PluginManager:
    """Discover and serve plugins to the pipeline engine."""

    def __init__(self, search_path: Optional[Path] = None):
        self._plugins: Dict[str, BasePlugin] = {}
        if search_path is not None:
            self.discover(search_path)

    # ------------------------------------------------------------------
    def discover(self, root: Path) -> None:
        """Discover plugins located beneath ``root``."""

        root = Path(root)
        if not root.exists():
            LOGGER.warning("Plugin directory %s does not exist", root)
            return

        for plugin_dir in root.iterdir():
            if not plugin_dir.is_dir():
                continue
            manifest_path = plugin_dir / "manifest.json"
            impl_path = plugin_dir / "plugin.py"
            if not (manifest_path.exists() and impl_path.exists()):
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                LOGGER.warning("Invalid manifest for plugin at %s", plugin_dir)
                continue
            plugin = self._load_plugin(impl_path, manifest)
            if plugin is not None:
                self.register(plugin)

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin instance with the manager."""

        self._plugins[plugin.plugin_id] = plugin

    def get_plugins_for_file(self, file_path: Path) -> List[BasePlugin]:
        applicable = [
            plugin
            for plugin in self._plugins.values()
            if plugin.can_process(file_path)
        ]
        if not applicable:
            return []

        graph = {plugin.plugin_id: list(plugin.requires) for plugin in applicable}
        sorter = TopologicalSorter(graph)
        try:
            ordered_ids = list(sorter.static_order())
        except CycleError as exc:  # pragma: no cover - configuration error
            LOGGER.error("Plugin dependency cycle detected: %s", exc)
            raise

        mapping = {plugin.plugin_id: plugin for plugin in applicable}
        return [mapping[pid] for pid in ordered_ids if pid in mapping]

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        return dict(self._plugins)

    # ------------------------------------------------------------------
    def _load_plugin(self, module_path: Path, manifest: dict) -> Optional[BasePlugin]:
        spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
        if spec is None or spec.loader is None:
            LOGGER.warning("Unable to load plugin module at %s", module_path)
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "register"):
            LOGGER.warning("Plugin module %s lacks a register() function", module_path)
            return None
        plugin = module.register(manifest)
        if not isinstance(plugin, BasePlugin):
            LOGGER.warning("register() at %s did not return a BasePlugin", module_path)
            return None
        return plugin


__all__ = ["PluginManager"]

