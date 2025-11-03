# ERROR_PIPELINE_MOD - Validation Pipeline GUI

A deterministic, plugin-based file validation system with a Windows desktop GUI. Automatically validates and fixes files using configurable plugins (Ruff, Black, Pylint, ESLint, etc.) with incremental validation and comprehensive error reporting.

## Features

- 🎯 **Deterministic Validation**: Identical inputs always produce identical outputs
- 🔌 **Plugin Architecture**: Modular validators that are easy to add/remove
- 🖱️ **Drag-and-Drop GUI**: Simple desktop interface for batch processing (up to 10 files)
- ⚡ **Incremental Processing**: SHA-256-based change detection skips unchanged files
- 🔧 **Auto-Fix**: Plugins automatically fix issues where possible
- 📊 **Rich Reporting**: JSON per-file reports + aggregated JSONL logs
- 🔒 **Isolated Execution**: Each file processed in temporary directories
- 🆔 **Reproducible**: ULID run IDs, UTC timestamps, toolchain version capture

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.12+
- **RAM**: 4GB minimum
- **Disk Space**: 500MB for application + validator tools

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/DICKY1987/ERROR_PIPELINE_MOD.git
cd ERROR_PIPELINE_MOD
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Validator Tools
Install the external validation tools you want to use:

**Python Validators:**
```bash
pip install ruff black isort pylint mypy pyright bandit safety
```

**JavaScript Validators:**
```bash
npm install -g eslint prettier
```

**Other Validators:**
```bash
pip install yamllint codespell
npm install -g markdownlint-cli
```

## Quick Start

### Run the GUI Application
```bash
python main.py
```

### Basic Workflow
1. **Launch** the application
2. **Drag and drop** up to 10 files into the window
3. **Select** output folder for validated files
4. **Click** "Process Files"
5. **Review** results in the log window and JSON reports

## Project Structure

```
ERROR_PIPELINE_MOD/
├── src/
│   ├── core/              # Pipeline engine and plugin management
│   ├── plugins/           # Validator plugins
│   ├── gui/               # Desktop interface
│   └── utils/             # Utilities (logging, JSONL, hashing)
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── ARCHITECTURE.md        # Technical documentation
└── main.py               # Application entry point
```

## Core Design Principles

### 1. Determinism
- Environment scrubbing (remove proxies, set locale)
- SHA-256 content hashing
- No network access during validation
- Stable plugin ordering via topological sort

### 2. Isolation
- Files processed in temporary directories
- Original files never modified
- Each plugin execution is stateless
- Output files: `{name}_VALIDATED_{timestamp}_{runid}{ext}`

### 3. Atomicity
- JSONL rotation uses atomic file operations
- Plugin execution with timeout + exception handling
- Complete or rollback operations

### 4. Reproducibility
- ULID run IDs (sortable, unique)
- UTC timestamps (ISO 8601)
- Toolchain versions captured in every report

## Supported File Types

### Current Support
- **Python** (.py): Ruff, Black, isort, Pylint, mypy, pyright, Bandit
- **JavaScript/TypeScript** (.js, .ts): ESLint, Prettier
- **JSON** (.json): jq validation
- **YAML** (.yaml, .yml): yamllint
- **Markdown** (.md): markdownlint-cli, mdformat
- **All text files**: codespell (spelling checker)

### Security Scanning (all files)
- Bandit (Python security)
- Safety (Python dependencies)
- Semgrep (multi-language patterns)
- Gitleaks (secrets detection)

## Configuration

Edit `config.yaml` to customize:
- Enable/disable specific plugins
- Set output folder defaults
- Configure auto-fix behavior
- Adjust JSONL rotation size (default: 75KB)

## Report Format

### Per-File JSON Report
Each validated file gets a detailed JSON report:
```json
{
  "run_id": "01JB4C3GY7KQWX2VMRT8HSDFGH",
  "file_in": "C:/original/test.py",
  "file_out": "D:/output/test_VALIDATED_20251103_021527_01JB4C.py",
  "timestamp_utc": "2025-11-03T02:15:27.123456Z",
  "toolchain": {
    "python_black": "Black, 24.8.0",
    "python_ruff": "ruff 0.6.9"
  },
  "summary": {
    "plugins_run": 2,
    "total_errors": 1,
    "total_warnings": 3,
    "auto_fixed": 5
  }
}
```

### Aggregated JSONL Log
All validation events logged to `pipeline_errors.jsonl` with automatic rotation at 75KB.

## Plugin Development

Want to add a new validator? See [ARCHITECTURE.md](ARCHITECTURE.md) for the plugin development guide.

### Quick Plugin Template
```python
# src/plugins/my_validator/plugin.py
from ..base_plugin import BasePlugin, ValidationError

class MyValidatorPlugin(BasePlugin):
    def build_command(self, file_path):
        return ['my-tool', '--check', str(file_path)]
    
    def parse_output(self, stdout, stderr, returncode, file_path):
        # Parse tool output into ValidationError objects
        return errors

def register():
    return MyValidatorPlugin(Path(__file__).parent / 'manifest.json')
```

## Development Status

**Current Phase**: Phase 1 - Core Architecture ✅

See [Issue #1](https://github.com/DICKY1987/ERROR_PIPELINE_MOD/issues/1) for the complete implementation roadmap.

## Contributing

This is a personal project, but suggestions and bug reports are welcome! Please open an issue.

## License

[Specify your license here]

## Acknowledgments

Built with:
- Python 3.12
- Tkinter + tkinterdnd2
- Ruff, Black, isort, Pylint, mypy, pyright
- ESLint, Prettier, yamllint, markdownlint-cli

---

**Version**: 1.0.0-dev  
**Last Updated**: 2025-11-03  
**Maintainer**: DICKY1987