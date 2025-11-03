"""
Pytest Configuration
Version: 1.1.0
Date: 2025-11-02
Owner: Platform.Engineering

Shared fixtures and configuration for all test modules.
Ensures repository root is in sys.path for core package imports.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

import pytest

# Add repository root to Python path for core package imports
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return repository root for locating fixtures and assets."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def state_machine_definition() -> Dict[str, Dict[str, List[str]]]:
    """Contract-compliant execution states used across integration tests."""
    return {
        "PENDING": {
            "description": "Task defined but not started",
            "allowed_transitions": ["RUNNING", "SKIPPED", "CANCELLED"],
        },
        "RUNNING": {
            "description": "Task currently executing",
            "allowed_transitions": ["COMPLETED", "FAILED", "CANCELLED"],
        },
        "COMPLETED": {
            "description": "Task finished successfully",
            "allowed_transitions": [],
        },
        "FAILED": {
            "description": "Task failed validation or execution",
            "allowed_transitions": ["PENDING", "CANCELLED"],
        },
        "SKIPPED": {
            "description": "Task skipped due to conditional logic",
            "allowed_transitions": [],
        },
        "CANCELLED": {
            "description": "Task cancelled by user or system",
            "allowed_transitions": [],
        },
    }


@pytest.fixture(scope="session")
def task_graph_definition() -> Dict[str, object]:
    """Minimal DAG mirroring the execution contract for workflow runs."""
    return {
        "version": "1.0.0",
        "tasks": [
            {
                "id": "task_001_preflight",
                "dependencies": [],
                "priority": 10,
            },
            {
                "id": "task_002_run_init",
                "dependencies": ["task_001_preflight"],
                "priority": 9,
            },
            {
                "id": "task_003_planning",
                "dependencies": ["task_002_run_init"],
                "priority": 8,
            },
            {
                "id": "task_004_worktree_a",
                "dependencies": ["task_003_planning"],
                "priority": 7,
                "parallel_group": "worktrees",
            },
            {
                "id": "task_005_worktree_b",
                "dependencies": ["task_003_planning"],
                "priority": 7,
                "parallel_group": "worktrees",
            },
            {
                "id": "task_006_merge_prep",
                "dependencies": ["task_004_worktree_a", "task_005_worktree_b"],
                "priority": 6,
            },
        ],
    }
