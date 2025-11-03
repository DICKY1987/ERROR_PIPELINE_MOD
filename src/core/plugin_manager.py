"""Plugin discovery and execution scaffolding."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.utils.types import PluginManifest, PluginResult


class PluginManager:
    """Loads plugins from the ``src/plugins`` package and prepares them for use."""

    def __init__(self, plugins_path: Optional[Path] = None) -> None:
        self._plugins_path = plugins_path or Path(__file__).resolve().parent.parent / "plugins"
        self._plugins: Dict[str, BasePlugin] = {}

    def discover(self) -> None:
        """Search the plugins directory and register available plugins."""
        raise NotImplementedError("Plugin discovery has not been implemented")

    def get_plugins_for_file(self, file_path: Path) -> List["BasePlugin"]:
        """Return plugins applicable to the supplied file path."""
        raise NotImplementedError("Plugin filtering has not been implemented")

    def _load_plugin(self, manifest_path: Path) -> "BasePlugin":
        """Load a plugin using its manifest definition."""
        raise NotImplementedError("Plugin loading has not been implemented")

    def run_plugins(self, plugins: Iterable["BasePlugin"], file_path: Path) -> List[PluginResult]:
        """Execute the provided plugins sequentially."""
        raise NotImplementedError("Plugin execution has not been implemented")


class BasePlugin:
    """Base class for validator plugins referenced throughout the documentation."""

    plugin_id: str
    manifest: PluginManifest
    name: str

    def build_command(self, file_path: Path) -> List[str]:  # pragma: no cover - placeholder
        raise NotImplementedError

    def check_tool_available(self) -> bool:  # pragma: no cover - placeholder
        raise NotImplementedError

    def execute(self, file_path: Path) -> PluginResult:  # pragma: no cover - placeholder
        raise NotImplementedError
