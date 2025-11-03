"""Pipeline primitives exposed as a convenience import."""

from .cache import FileHashCache
from .engine import PipelineEngine, PipelineSummary
from .jsonl import JSONLRotatingLogger
from .plugins import BasePlugin, PluginError, PluginManager, PluginResult

__all__ = [
    "BasePlugin",
    "FileHashCache",
    "JSONLRotatingLogger",
    "PipelineEngine",
    "PipelineSummary",
    "PluginError",
    "PluginManager",
    "PluginResult",
]
