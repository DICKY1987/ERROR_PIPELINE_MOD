---
doc_key: ACMS_README
semver: 1.1.0
status: active
effective_date: 2025-11-02
owner: Platform.Engineering
---

# Autonomous Code Modification System (ACMS)

ACMS is a deterministic, headless pipeline that plans, executes, validates, and merges code changes using AI-first tooling. This repository captures Phase 1 of the multi-phase implementation described in the ACMS executive summary and supplemental development plan.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Git
- pip (comes with Python)

### Installation

**Option 1: Automated Setup (Recommended)**

```bash
# Linux/Mac
chmod +x setup_dev.sh
./setup_dev.sh

# Windows PowerShell
.\setup_dev.ps1
```

**Option 2: Manual Setup**

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# 5. Verify installation
pytest -v
```

## 📁 Repository Structure

```
.
├── core/                          # Core ACMS package
│   ├── __init__.py
│   ├── config.py
│   ├── state_machine.py          # Execution state machine
│   ├── task_scheduler.py         # DAG topological sort
│   └── orchestrator.py           # Main pipeline orchestrator
├── tests/                         # Test suite
│   ├── conftest.py               # Shared fixtures
│   ├── integration/              # Integration tests
│   └── test_worktree.py          # Worktree management tests
├── immediate CI enforcement and reproducibility/
│   ├── conftest.py               # Path configuration for tests
│   ├── test_state_machine.py    # State machine tests
│   ├── test_toposort.py          # Topological sort tests
│   └── schemas/                  # JSON schemas
├── docs/                          # Documentation
├── .github/
│   └── workflows/
│       └── ci.yml                # CI/CD pipeline
├── .env.example                   # Environment variables template
├── .gitignore
├── docker-compose.yml
├── LICENSE
├── noxfile.py                     # Task automation
├── pyproject.toml                 # Package configuration
├── README.md                      # This file
├── requirements.txt               # Production dependencies
├── setup_dev.sh                   # Linux/Mac setup script
└── setup_dev.ps1                  # Windows setup script
```

## 🧪 Running Tests

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Files

```bash
# State machine tests
pytest "immediate CI enforcement and reproducibility/test_state_machine.py" -v

# Topological sort tests
pytest "immediate CI enforcement and reproducibility/test_toposort.py" -v

# Worktree tests
pytest tests/test_worktree.py -v

# Integration tests only
pytest tests/integration/ -v -m integration
```

### Run with Coverage

```bash
pytest --cov=core --cov-report=term --cov-report=html
```

Coverage report will be available in `htmlcov/index.html`

## 🔧 Development Tools

### Linting

```bash
# Black formatting
black .

# Ruff linting
ruff check .

# Check import sorting
isort --check-only .
```

### Type Checking

```bash
mypy core/
```

### Run All Quality Checks

```bash
# Format code
black .
isort .

# Lint
ruff check . --fix

# Type check
mypy core/

# Test
pytest -v --cov=core
```

## 🐛 Troubleshooting

### Import Errors: `ModuleNotFoundError: No module named 'core'`

**Solution**: Ensure the package is installed in editable mode:

```bash
pip install -e ".[dev]"
```

This is the recommended approach and is now properly configured in:
- `pyproject.toml` - with proper test paths
- `.github/workflows/ci.yml` - CI/CD installs package before testing
- `tests/conftest.py` - adds repo root to sys.path as backup
- `immediate CI enforcement and reproducibility/conftest.py` - same for reference tests

### Tests Pass Locally But Fail in CI

Verify your local setup matches CI:
1. Clean install: `rm -rf .venv && python -m venv .venv`
2. Activate: `source .venv/bin/activate`
3. Install: `pip install -e ".[dev]"`
4. Test: `pytest -v`

### IDE Not Recognizing Imports

1. Restart your IDE after installing in editable mode
2. In VSCode: Reload window (Cmd/Ctrl+Shift+P → "Developer: Reload Window")
3. In PyCharm: Mark project root as "Sources Root"

## 📚 Documentation

- [Executive Summary](ACMS_EXECUTIVE_SUMMARY.md) - Project overview and architecture
- [Build Execution Contract](ACMS_BUILD_EXECUTION_CONTRACT.yaml) - Implementation phases
- [Test Import Fix Guide](ACMS_TEST_IMPORT_FIX_GUIDE.md) - Detailed fix documentation
- [Versioning Operating Contract](VERSIONING_OPERATING_CONTRACT.md) - Governance

## 🔄 CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Lint and Test**: Runs formatting, linting, and all tests
- **Type Check**: Static type checking with mypy
- **Security Scans**: Bandit and Gitleaks for security
- **Integration Tests**: Full workflow tests

All checks must pass before merging.

## 🌟 Key Features

### Phase 1 Deliverables (Completed)

✅ Version-controlled licensing and documentation  
✅ Python package metadata via `pyproject.toml`  
✅ Task automation entry point using Nox  
✅ Core Python package with proper structure  
✅ Environment and container orchestration templates  
✅ CI/CD pipeline with comprehensive checks  
✅ **Fixed test import issues** - all tests pass reliably

## 🚦 Getting Started Checklist

- [ ] Clone repository
- [ ] Run setup script (`./setup_dev.sh` or `.\setup_dev.ps1`)
- [ ] Copy `.env.example` to `.env` and configure
- [ ] Run tests to verify setup: `pytest -v`
- [ ] Review documentation in `docs/`
- [ ] Read the [Executive Summary](ACMS_EXECUTIVE_SUMMARY.md)

## 📝 Contributing

1. Create a feature branch from `develop`
2. Make your changes
3. Run quality checks: `black . && ruff check . && pytest -v`
4. Commit with descriptive messages
5. Push and create a pull request

All PRs must:
- Pass CI/CD checks
- Maintain test coverage >= 80%
- Follow code style (Black, Ruff)
- Include tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/acms/issues)
- **Documentation**: See `docs/` directory
- **Questions**: Contact platform engineering team

## 📈 Next Steps

Subsequent phases will add:
- Orchestration framework (Phase 2)
- Plugin management (Phase 3)
- LLM tool integration (Phase 4)
- Validation gates (Phase 5)
- Worktree management (Phase 6)
- Observability and tracing (Phase 7)
- CI/CD integration (Phase 8)
- Full test coverage (Phase 9)
- Documentation generation (Phase 10)
- Deployment automation (Phase 11)

See [ACMS_BUILD_EXECUTION_CONTRACT.yaml](ACMS_BUILD_EXECUTION_CONTRACT.yaml) for the complete roadmap.

---

*Last Updated: 2025-11-02*  
*Version: 1.1.0*  
*Owner: Platform.Engineering*
