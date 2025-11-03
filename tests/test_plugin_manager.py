"""Unit tests for plugin ordering and dependency handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline.plugins import BasePlugin, PluginError, PluginManager, PluginResult


class AlphaPlugin(BasePlugin):
    plugin_id = "alpha"

    def run(self, file_path: Path, state):
        return PluginResult(plugin_id=self.plugin_id, produced=file_path)


class BetaPlugin(BasePlugin):
    plugin_id = "beta"
    requires = ("alpha",)

    def run(self, file_path: Path, state):
        return PluginResult(plugin_id=self.plugin_id, produced=file_path)


class GammaPlugin(BasePlugin):
    plugin_id = "gamma"
    requires = ("beta",)

    def run(self, file_path: Path, state):
        return PluginResult(plugin_id=self.plugin_id, produced=file_path)


def test_plugins_execute_in_dependency_order(tmp_path: Path) -> None:
    file_path = tmp_path / "example.txt"
    file_path.write_text("data", encoding="utf-8")

    manager = PluginManager([GammaPlugin(), AlphaPlugin(), BetaPlugin()])
    order = [plugin.plugin_id for plugin in manager.ordered_plugins(file_path)]
    assert order == ["alpha", "beta", "gamma"]


def test_cycle_detection_raises_error(tmp_path: Path) -> None:
    class CycleA(BasePlugin):
        plugin_id = "cycle_a"
        requires = ("cycle_c",)

        def run(self, file_path: Path, state):
            return PluginResult(plugin_id=self.plugin_id, produced=file_path)

    class CycleB(BasePlugin):
        plugin_id = "cycle_b"
        requires = ("cycle_a",)

        def run(self, file_path: Path, state):
            return PluginResult(plugin_id=self.plugin_id, produced=file_path)

    class CycleC(BasePlugin):
        plugin_id = "cycle_c"
        requires = ("cycle_b",)

        def run(self, file_path: Path, state):
            return PluginResult(plugin_id=self.plugin_id, produced=file_path)

    manager = PluginManager([CycleA(), CycleB(), CycleC()])
    file_path = tmp_path / "example.txt"
    file_path.write_text("data", encoding="utf-8")

    with pytest.raises(PluginError):
        manager.ordered_plugins(file_path)
