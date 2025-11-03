"""Discovery and management of validation pipeline plugins."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from src.plugins.base_plugin import BasePlugin, ManifestError, PluginError


class PluginLoadError(PluginError):
    """Raised when a plugin module cannot be imported or instantiated."""


class PluginManager:
    """Manage discovery and loading of pipeline plugins."""

    def __init__(self, plugins_dir: Path | None = None) -> None:
        self._plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).resolve().parents[1] / "plugins"
        self._manifests: Dict[str, Mapping[str, Any]] = {}
        self._plugin_dirs: Dict[str, Path] = {}
        self._dependencies: Dict[str, Sequence[str]] = {}
        self._load_order: List[str] = []
        self._instances: Dict[str, BasePlugin] = {}

    @property
    def plugins_dir(self) -> Path:
        return self._plugins_dir

    @property
    def manifests(self) -> Mapping[str, Mapping[str, Any]]:
        if not self._manifests:
            self.discover()
        return self._manifests

    @property
    def dependency_graph(self) -> Mapping[str, Sequence[str]]:
        if not self._dependencies:
            self.discover()
        return self._dependencies

    @property
    def load_order(self) -> Sequence[str]:
        if not self._load_order:
            self.discover()
        return tuple(self._load_order)

    def discover(self) -> None:
        """Locate plugin manifests and compute dependency ordering."""

        manifest_paths = sorted(self._plugins_dir.glob("*/manifest.json"))
        manifests: Dict[str, Mapping[str, Any]] = {}
        plugin_dirs: Dict[str, Path] = {}
        dependencies: Dict[str, Sequence[str]] = {}

        for manifest_path in manifest_paths:
            manifest = BasePlugin.load_manifest(manifest_path)
            name = manifest["name"]  # load_manifest ensures field exists

            if name in manifests:
                raise ManifestError(f"Duplicate plugin name detected: {name}")

            plugin_dir = manifest_path.parent
            plugin_dirs[name] = plugin_dir

            raw_dependencies = manifest.get("dependencies", [])
            if not isinstance(raw_dependencies, Iterable):  # pragma: no cover - defensive
                raise ManifestError("'dependencies' field must be iterable")

            validated_dependencies: List[str] = []
            for dependency in raw_dependencies:
                if not isinstance(dependency, str):
                    raise ManifestError(
                        f"Dependency entries must be strings - plugin '{name}' references invalid entry"
                    )
                validated_dependencies.append(dependency)

            manifests[name] = manifest
            dependencies[name] = tuple(validated_dependencies)

        for name, deps in dependencies.items():
            for dependency in deps:
                if dependency not in manifests:
                    raise ManifestError(
                        f"Plugin '{name}' declares unknown dependency '{dependency}'"
                    )

        sorter = TopologicalSorter(dependencies)
        try:
            order = list(sorter.static_order())
        except CycleError as exc:  # pragma: no cover - CycleError unlikely in example
            cycle = " -> ".join(exc.args[1]) if len(exc.args) > 1 else str(exc)
            raise ManifestError(f"Cyclic plugin dependency detected: {cycle}") from exc

        self._manifests = manifests
        self._plugin_dirs = plugin_dirs
        self._dependencies = dependencies
        self._load_order = order
        self._instances.clear()

    def load_plugins(self) -> Sequence[BasePlugin]:
        """Import and instantiate all discovered plugins in dependency order."""

        if not self._load_order:
            self.discover()

        for name in self._load_order:
            if name in self._instances:
                continue

            module = self._import_plugin_module(name, self._plugin_dirs[name])
            plugin_cls = self._resolve_plugin_class(module, self._manifests[name])

            try:
                instance = plugin_cls(self._manifests[name], self._plugin_dirs[name])
            except TypeError as exc:
                raise PluginLoadError(f"Failed to instantiate plugin '{name}': {exc}") from exc

            self._instances[name] = instance

        return tuple(self._instances[name] for name in self._load_order)

    def get_plugin(self, name: str) -> BasePlugin:
        if name not in self._instances:
            self.load_plugins()
        try:
            return self._instances[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise PluginLoadError(f"Plugin '{name}' is not loaded") from exc

    def _import_plugin_module(self, name: str, plugin_dir: Path) -> ModuleType:
        module_name = f"src.plugins.{plugin_dir.name}.plugin"
        plugin_path = plugin_dir / "plugin.py"

        if not plugin_path.exists():
            raise PluginLoadError(f"Plugin '{name}' missing plugin.py module")

        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Unable to load specification for plugin '{name}'")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 - propagate detailed error information
            raise PluginLoadError(f"Error importing plugin '{name}': {exc}") from exc

        return module

    def _resolve_plugin_class(self, module: ModuleType, manifest: Mapping[str, Any]) -> type[BasePlugin]:
        entrypoint = manifest.get("entrypoint", "Plugin")

        if not isinstance(entrypoint, str):
            raise ManifestError("Manifest 'entrypoint' must be a string when provided")

        candidate = getattr(module, entrypoint, None)
        if self._is_valid_plugin_class(candidate):
            return candidate

        for attr in module.__dict__.values():
            if self._is_valid_plugin_class(attr):
                return attr

        raise PluginLoadError(
            "Plugin module does not expose a BasePlugin subclass via the declared entrypoint"
        )

    @staticmethod
    def _is_valid_plugin_class(obj: Any) -> bool:
        return inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj is not BasePlugin
