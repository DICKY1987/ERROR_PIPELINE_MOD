"""
Pytest Configuration for Reference Implementations
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

This conftest.py adds the repository root to sys.path to enable
imports of the core package from test modules in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add repository root to Python path for core package imports
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Optional: Print confirmation for debugging (remove in production)
# print(f"✓ Added {repo_root} to sys.path")
