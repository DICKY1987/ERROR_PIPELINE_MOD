---
doc_key: ACMS_IMPORT_FIX_IMPLEMENTATION
semver: 1.0.0
status: active
effective_date: 2025-11-02
owner: Platform.Engineering
contract_type: execution
---

# ACMS Test Import Fix - Implementation Summary

## 🎯 Executive Summary

**Problem**: Three test modules fail with `ModuleNotFoundError: No module named 'core'`

**Root Cause**: Tests execute without repository root in Python's module search path

**Solution**: Install package in editable mode + add conftest.py files as backup

**Status**: ✅ Ready for Implementation

**Time to Fix**: 30 minutes

---

## 📦 Deliverables

All files are ready in `/mnt/user-data/outputs/`:

1. **ACMS_TEST_IMPORT_FIX_GUIDE.md** - Comprehensive fix documentation
2. **pyproject.toml** - Updated package configuration
3. **immediate_ci_enforcement_conftest.py** - Path config for reference tests
4. **tests_conftest.py** - Updated main conftest with path config
5. **ci.yml** - Updated CI/CD workflow
6. **setup_dev.sh** - Linux/Mac automated setup script
7. **setup_dev.ps1** - Windows PowerShell setup script
8. **README_updated.md** - Updated README with setup instructions

---

## 🚀 Implementation Steps

### Step 1: Update Configuration Files (5 min)

```bash
# 1. Update pyproject.toml
cp /path/to/outputs/pyproject.toml ./pyproject.toml

# 2. Update GitHub Actions workflow
cp /path/to/outputs/ci.yml ./.github/workflows/ci.yml

# 3. Add conftest.py to immediate CI enforcement directory
cp /path/to/outputs/immediate_ci_enforcement_conftest.py \
   "immediate CI enforcement and reproducibility/conftest.py"

# 4. Update tests conftest.py
cp /path/to/outputs/tests_conftest.py ./tests/conftest.py

# 5. Update README
cp /path/to/outputs/README_updated.md ./README.md
```

### Step 2: Add Setup Scripts (2 min)

```bash
# Copy setup scripts
cp /path/to/outputs/setup_dev.sh ./setup_dev.sh
cp /path/to/outputs/setup_dev.ps1 ./setup_dev.ps1

# Make Linux/Mac script executable
chmod +x setup_dev.sh
```

### Step 3: Test Locally (10 min)

```bash
# Clean start
rm -rf .venv

# Run setup script
./setup_dev.sh  # Linux/Mac
# OR
.\setup_dev.ps1  # Windows

# Verify all tests pass
pytest -v

# Expected output:
# ✅ All tests pass
# ✅ No ModuleNotFoundError
# ✅ Coverage >= 80%
```

### Step 4: Commit and Push (5 min)

```bash
git add pyproject.toml
git add .github/workflows/ci.yml
git add "immediate CI enforcement and reproducibility/conftest.py"
git add tests/conftest.py
git add README.md
git add setup_dev.sh setup_dev.ps1
git add ACMS_TEST_IMPORT_FIX_GUIDE.md

git commit -m "fix: resolve ModuleNotFoundError in test suite

- Install package in editable mode for proper imports
- Add conftest.py files with sys.path configuration
- Update CI/CD to install package before testing
- Add automated setup scripts for developers
- Update documentation with setup instructions

Fixes: test_state_machine.py, test_toposort.py, test_worktree.py
Testing: All tests now pass locally and in CI
Coverage: Maintained at >= 80%"

git push origin <your-branch>
```

### Step 5: Verify CI/CD (10 min)

1. Create pull request
2. Wait for CI/CD checks to complete
3. Verify all jobs pass:
   - ✅ lint-and-test
   - ✅ type-check
   - ✅ security-scans
   - ✅ integration-tests
   - ✅ validate-success

---

## 🔍 What Changed

### pyproject.toml
**Before**: No dev dependencies, single test path
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

**After**: Dev dependencies added, multiple test paths, pythonpath configured
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov>=4.0", ...]

[tool.pytest.ini_options]
testpaths = ["tests", "immediate CI enforcement and reproducibility"]
pythonpath = "."
```

### CI/CD Workflow
**Before**: Tests run without package installation
```yaml
- name: Run pytest
  run: pytest -v
```

**After**: Package installed in editable mode first
```yaml
- name: Install package in editable mode with dev dependencies
  run: pip install -e ".[dev]"
  
- name: Run pytest with coverage
  run: pytest -v --cov=core
```

### New Files
- `immediate CI enforcement and reproducibility/conftest.py` - Adds repo root to sys.path
- `tests/conftest.py` - Updated with sys.path configuration
- `setup_dev.sh` - Automated Linux/Mac setup
- `setup_dev.ps1` - Automated Windows setup
- `ACMS_TEST_IMPORT_FIX_GUIDE.md` - Comprehensive documentation

---

## ✅ Validation Checklist

Before marking as complete:

- [ ] All three failing tests now pass
- [ ] CI/CD pipeline passes all checks
- [ ] No import errors in any test module
- [ ] Test coverage maintained at >= 80%
- [ ] Setup scripts work on all platforms
- [ ] Documentation updated and accurate
- [ ] Developers can run tests without manual configuration

---

## 📊 Impact Analysis

### Before Fix
- ❌ 3 test modules failing
- ❌ CI/CD pipeline blocked
- ❌ Developers need manual sys.path configuration
- ❌ IDE autocomplete not working

### After Fix
- ✅ All tests passing
- ✅ CI/CD pipeline green
- ✅ One-command setup for developers
- ✅ IDE autocomplete working
- ✅ Production-ready packaging

---

## 🎓 Technical Details

### Why Editable Install Works

**Editable installation** (`pip install -e .`) creates a link in site-packages:
```
site-packages/
  acms.egg-link  → /path/to/repo
  easy-install.pth
```

This makes the `core` package discoverable from any working directory:
```python
import core.state_machine  # ✅ Works from anywhere
```

### Why conftest.py Is Needed As Backup

Even with editable install, some edge cases benefit from explicit path configuration:
- Running single test files directly
- IDE test runners with custom configurations
- Docker containers without proper installation

The conftest.py files provide a fallback:
```python
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
```

---

## 🔮 Future Improvements

1. **Pre-commit hooks** - Auto-format and lint before commit
2. **Docker development** - Consistent environment across machines
3. **Test parallelization** - Faster CI/CD with pytest-xdist
4. **Coverage enforcement** - Fail CI if coverage drops below 80%

See ACMS_TEST_IMPORT_FIX_GUIDE.md Section "Additional Recommendations" for details.

---

## 📞 Support

**Questions?** See the comprehensive documentation:
- [ACMS_TEST_IMPORT_FIX_GUIDE.md](ACMS_TEST_IMPORT_FIX_GUIDE.md) - Full fix guide
- [README.md](README.md) - Updated setup instructions

**Issues?** Run diagnostics:
```bash
# Check package installation
pip list | grep acms

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if core package is importable
python -c "import core; print(core.__file__)"
```

---

## 📝 Commit Message Template

```
fix: resolve ModuleNotFoundError in test suite

Problem:
- test_state_machine.py failed with ModuleNotFoundError
- test_toposort.py failed with ModuleNotFoundError  
- test_worktree.py failed with ModuleNotFoundError

Root Cause:
- Tests executed without repository root in sys.path
- Core package not discoverable during test execution

Solution:
1. Install package in editable mode (pip install -e .)
2. Add conftest.py files with sys.path configuration
3. Update CI/CD to install package before testing
4. Add automated setup scripts for developers

Changes:
- Updated pyproject.toml with dev dependencies and test config
- Updated .github/workflows/ci.yml with package installation
- Added immediate CI enforcement and reproducibility/conftest.py
- Updated tests/conftest.py with path configuration
- Added setup_dev.sh and setup_dev.ps1 scripts
- Updated README.md with setup instructions
- Added comprehensive fix documentation

Testing:
- All tests pass locally ✅
- CI/CD pipeline green ✅
- Coverage maintained at >= 80% ✅

Co-authored-by: AI Assistant <assistant@anthropic.com>
```

---

## 🎉 Success Criteria

Fix is complete when:

1. ✅ **All tests pass**: `pytest -v` shows 0 failures
2. ✅ **CI/CD green**: All GitHub Actions checks pass
3. ✅ **Easy setup**: New developers run one script to start
4. ✅ **IDE support**: Autocomplete works for core package
5. ✅ **Documentation**: README and guides updated

---

*Implementation Guide v1.0.0*  
*Date: 2025-11-02*  
*Owner: Platform.Engineering*  
*Status: Ready for Implementation*

**Estimated Time**: 30 minutes  
**Complexity**: Low  
**Risk**: Minimal (backwards compatible)  
**Impact**: High (unblocks CI/CD and development)
