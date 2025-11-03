"""Plugin management utilities for the validation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class PluginResult:
    """Container describing the outcome of a plugin execution."""

    plugin_id: str
    produced: Optional[Path]
    errors: List[Dict[str, object]] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)


class PluginError(RuntimeError):
    """Raised when plugin registration or execution fails."""


class BasePlugin:
    """Base class for pipeline plugins."""

    plugin_id: str = ""
    name: str = ""
    requires: Sequence[str] = ()
    provides: Sequence[str] = ()

    def applies_to(self, file_path: Path) -> bool:
        """Return ``True`` if this plugin should run for ``file_path``."""

        return True

    def run(self, file_path: Path, state: Dict[str, object]) -> PluginResult:
        """Execute the plugin.

        Subclasses must override this method.
        """

        raise NotImplementedError


class PluginManager:
    """Registers plugins and resolves execution order."""

    def __init__(self, plugins: Optional[Iterable[BasePlugin]] = None) -> None:
        self._plugins: Dict[str, BasePlugin] = {}
        if plugins:
            for plugin in plugins:
                self.register(plugin)

    def register(self, plugin: BasePlugin) -> None:
        if not plugin.plugin_id:
            raise PluginError("Plugin must define a plugin_id")
        if plugin.plugin_id in self._plugins:
            raise PluginError(f"Plugin '{plugin.plugin_id}' already registered")
        self._plugins[plugin.plugin_id] = plugin

    def get(self, plugin_id: str) -> BasePlugin:
        try:
            return self._plugins[plugin_id]
        except KeyError as exc:
            raise PluginError(f"Unknown plugin '{plugin_id}'") from exc

    def applicable_plugins(self, file_path: Path) -> List[BasePlugin]:
        return [
            plugin
            for plugin in self._plugins.values()
            if plugin.applies_to(file_path)
        ]

    def ordered_plugins(self, file_path: Path) -> List[BasePlugin]:
        applicable = self.applicable_plugins(file_path)
        graph: Dict[str, Sequence[str]] = {
            plugin.plugin_id: tuple(plugin.requires) for plugin in applicable
        }

        sorter = TopologicalSorter(graph)
        try:
            ordered_ids = list(sorter.static_order())
        except CycleError as exc:
            raise PluginError("Cycle detected in plugin dependency graph") from exc

        ordered_plugins = [self.get(plugin_id) for plugin_id in ordered_ids]
        return ordered_plugins

    def execute(self, file_path: Path, state: Optional[Dict[str, object]] = None) -> List[PluginResult]:
        state = state or {}
        results: List[PluginResult] = []
        for plugin in self.ordered_plugins(file_path):
            result = plugin.run(file_path, state)
            if not isinstance(result, PluginResult):
                raise PluginError(
                    f"Plugin '{plugin.plugin_id}' returned unexpected result: {result!r}"
                )
            results.append(result)
        return results


__all__ = [
    "BasePlugin",
    "PluginError",
    "PluginManager",
    "PluginResult",
]
