---
doc_key: ACMS_TEST_IMPORT_FIX_GUIDE
semver: 1.0.0
status: active
effective_date: 2025-11-02
owner: Platform.Engineering
contract_type: intent
---

# ACMS Test Import Error Fix Guide

## Executive Summary

**Problem**: Three test modules fail with `ModuleNotFoundError: No module named 'core'`
- `immediate CI enforcement and reproducibility/test_state_machine.py`
- `immediate CI enforcement and reproducibility/test_toposort.py`
- `tests/test_worktree.py`

**Root Cause**: Tests execute with their containing directory in `sys.path` instead of repository root, preventing Python from resolving the `core` package.

**Impact**: CI/CD pipeline fails, blocking automated testing and deployment.

---

## Solution 1: Install Package in Editable Mode ⭐ **(RECOMMENDED)**

This is the most robust, production-ready approach that aligns with Python packaging best practices.

### Implementation Steps

#### 1.1 Update pyproject.toml

Add development dependencies and ensure proper package configuration:

```toml
# Add to existing pyproject.toml

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.5",
]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q -v"
testpaths = [
    "tests",
    "immediate CI enforcement and reproducibility"
]
pythonpath = "."
```

#### 1.2 Install Package in Development Environment

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or if using requirements.txt
pip install -e .
pip install -r requirements.txt
```

#### 1.3 Update CI/CD Pipeline

Modify `.github/workflows/ci.yml` to install package before testing:

```yaml
- name: Install Dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -e ".[dev]"  # Install in editable mode
    
- name: Run pytest
  run: pytest -v
```

### Benefits
✅ **Production-ready**: Follows Python packaging standards  
✅ **IDE support**: Better autocomplete and type checking  
✅ **Portable**: Works across all environments consistently  
✅ **CI/CD compatible**: Integrates seamlessly with automation  
✅ **No sys.path hacks**: Clean, maintainable solution

---

## Solution 2: Add Conftest to Set Python Path

Create a conftest.py file that adds the repository root to `sys.path`.

### Implementation Steps

#### 2.1 Create Root-Level conftest.py

Create `immediate CI enforcement and reproducibility/conftest.py`:

```python
"""
Pytest configuration for reference implementations
Adds repository root to Python path for core package imports
"""
import sys
from pathlib import Path

# Add repository root to Python path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
```

#### 2.2 Update Existing tests/conftest.py

Add the same path configuration to `tests/conftest.py`:

```python
"""
Pytest Configuration
Version: 1.0.0
Date: 2025-11-02
Shared fixtures and configuration
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

import pytest

# Add repository root to Python path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# ... rest of existing fixtures ...
```

### Benefits
✅ **Quick fix**: Minimal changes required  
✅ **No installation needed**: Works immediately  
✅ **Pytest-specific**: Only affects test execution

### Drawbacks
⚠️ **Non-standard**: Not following Python packaging best practices  
⚠️ **IDE issues**: May not help with IDE autocomplete  
⚠️ **Maintenance burden**: Multiple conftest files to maintain

---

## Solution 3: Reorganize Test Structure

Move reference implementation tests into the standard test directory structure.

### Implementation Steps

#### 3.1 Create New Test Directory Structure

```bash
mkdir -p tests/reference_implementations
mkdir -p tests/unit
mkdir -p tests/integration
```

#### 3.2 Move Test Files

```bash
# Move reference implementation tests
mv "immediate CI enforcement and reproducibility/test_state_machine.py" \
   tests/reference_implementations/

mv "immediate CI enforcement and reproducibility/test_toposort.py" \
   tests/reference_implementations/

# Keep test_worktree.py in tests/ (already there)
```

#### 3.3 Update pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q -v"
testpaths = [
    "tests",
]
pythonpath = "."
```

#### 3.4 Update README in Reference Directory

Create `immediate CI enforcement and reproducibility/README.md`:

```markdown
# Reference Implementations

This directory contains reference implementations and schemas.
Test files have been moved to `tests/reference_implementations/` to align 
with the project's standard test structure.

## Contents
- `schemas/` - JSON schemas for contracts
- `core/` - Reference implementation modules
- `tools/` - Utility scripts

## Running Tests
```bash
pytest tests/reference_implementations/ -v
```
```

### Benefits
✅ **Clean structure**: Single, organized test directory  
✅ **Standard layout**: Follows pytest best practices  
✅ **Easy discovery**: All tests in expected location

### Drawbacks
⚠️ **File relocation**: Changes existing structure  
⚠️ **Documentation updates**: Need to update references

---

## Solution 4: Use PYTHONPATH Environment Variable

Set PYTHONPATH to include repository root before running tests.

### Implementation Steps

#### 4.1 Local Development

```bash
# Linux/Mac
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest -v

# Windows (CMD)
set PYTHONPATH=%PYTHONPATH%;%CD%
pytest -v

# Windows (PowerShell)
$env:PYTHONPATH="$env:PYTHONPATH;$(Get-Location)"
pytest -v
```

#### 4.2 Update CI/CD Pipeline

```yaml
- name: Run pytest
  env:
    PYTHONPATH: ${{ github.workspace }}
  run: pytest -v
```

#### 4.3 Create Helper Script

Create `run_tests.sh`:

```bash
#!/bin/bash
# Set PYTHONPATH and run tests

export PYTHONPATH="${PYTHONPATH}:$(dirname "$0")"
pytest "$@"
```

### Benefits
✅ **No code changes**: Environment-only solution  
✅ **Flexible**: Easy to adjust per environment

### Drawbacks
⚠️ **Environment-dependent**: Must be set consistently  
⚠️ **Easy to forget**: Developers must remember to set it  
⚠️ **Not portable**: Doesn't work in all IDEs

---

## Solution 5: Use pytest -m Option

Run pytest from repository root using python module execution.

### Implementation Steps

#### 5.1 Update Test Execution Commands

Instead of:
```bash
pytest
```

Use:
```bash
python -m pytest
```

#### 5.2 Update CI/CD Pipeline

```yaml
- name: Run pytest
  run: python -m pytest tests/ "immediate CI enforcement and reproducibility/" -v
```

#### 5.3 Update Documentation

Update README.md and development guides to use `python -m pytest`.

### Benefits
✅ **Simple**: Minimal configuration  
✅ **Standard**: Uses Python module execution  
✅ **No installation**: Works without editable install

### Drawbacks
⚠️ **Convention change**: Requires updating habits  
⚠️ **IDE integration**: Some IDEs may not auto-detect

---

## Recommended Implementation Plan

### Phase 1: Immediate Fix (Day 1)
1. **Implement Solution 1** (editable install) as the primary fix
2. **Update CI/CD pipeline** to install package before testing
3. **Update developer documentation** with setup instructions

### Phase 2: Structural Improvements (Day 2-3)
1. **Implement Solution 3** (reorganize tests) for better structure
2. **Update all test import paths** if needed
3. **Update documentation** to reflect new structure

### Phase 3: Validation (Day 3-4)
1. **Run full test suite** locally
2. **Verify CI/CD pipeline** passes all checks
3. **Update ACMS_EXECUTIVE_SUMMARY.md** to reflect fixes

---

## Testing the Fix

### Local Validation

```bash
# 1. Install package in editable mode
pip install -e ".[dev]"

# 2. Run all tests
pytest -v

# 3. Run specific test modules
pytest "immediate CI enforcement and reproducibility/test_state_machine.py" -v
pytest "immediate CI enforcement and reproducibility/test_toposort.py" -v
pytest tests/test_worktree.py -v

# 4. Check coverage
pytest --cov=core --cov-report=term --cov-report=html
```

### CI/CD Validation

```bash
# Simulate CI environment locally
git clone <repo-url> acms-test
cd acms-test
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest -v
```

---

## Additional Recommendations

### 1. Update requirements.txt

Ensure all test dependencies are included:

```txt
# Core dependencies
pytest>=7.0
pytest-cov>=4.0
pytest-testinfra>=9.0

# Linting and formatting
black>=23.0
ruff>=0.1.0
isort>=5.12.0

# Type checking
mypy>=1.5
types-requests

# Testing utilities
pytest-mock>=3.11.0
pytest-timeout>=2.1.0
```

### 2. Add Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### 3. Update Developer Documentation

Add to README.md:

```markdown
## Development Setup

1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `source .venv/bin/activate`
4. Install in editable mode: `pip install -e ".[dev]"`
5. Run tests: `pytest -v`

## Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_worktree.py -v

# Run with coverage
pytest --cov=core --cov-report=term
```
```

### 4. IDE Configuration

#### VSCode settings.json

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "-v",
        "--no-cov"
    ],
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}
```

#### PyCharm Configuration

1. Mark project root as "Sources Root"
2. Enable pytest as test runner
3. Add repository root to PYTHONPATH in run configurations

---

## Validation Checklist

Before considering this issue resolved, verify:

- [ ] All three failing tests pass locally
- [ ] CI/CD pipeline runs successfully
- [ ] No import errors in any test modules
- [ ] Test coverage maintained at >= 80%
- [ ] IDE autocomplete works for core package
- [ ] Documentation updated with new setup instructions
- [ ] All developers can run tests without configuration
- [ ] Pre-commit hooks configured (optional but recommended)

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'core'" persists

**Solution**: Verify package installation
```bash
pip list | grep acms
# Should show: acms 0.1.0 <path-to-repo>
```

### Issue: "ImportError: cannot import name 'ExecutionStateMachine'"

**Solution**: Check if module exists
```bash
python -c "import core.state_machine; print(core.state_machine.__file__)"
```

### Issue: Tests pass locally but fail in CI

**Solution**: Ensure CI installs package
```yaml
- name: Install package
  run: pip install -e .
```

### Issue: IDE doesn't recognize imports

**Solution**: Restart IDE after installing in editable mode, or mark repository root as sources root.

---

## References

- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Setuptools Documentation](https://setuptools.pypa.io/)
- ACMS_EXECUTIVE_SUMMARY.md
- ACMS_BUILD_EXECUTION_CONTRACT.yaml

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-02 | Platform.Engineering | Initial comprehensive fix guide |

---

*This document is part of the ACMS governance framework and follows the versioning operating contract.*
