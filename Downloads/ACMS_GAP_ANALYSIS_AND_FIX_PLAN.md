---
doc_key: ACMS_GAP_ANALYSIS_FIX_PLAN
semver: 1.0.0
status: active
effective_date: 2025-11-02
owner: Platform.Engineering
contract_type: intent
---

# ACMS Gap Analysis & Remediation Plan

## Executive Summary

The ACMS repository has **partially implemented** the Build Execution Contract. While foundational scaffolding, orchestration core logic, worktree management, context broker, observability, CI/CD, and deployment infrastructure are present, **three critical delivery gaps** prevent full contract compliance:

1. **Phase 2 State Machine Governance** - Missing schema and dedicated unit tests
2. **Phase 3 Plugin System Scaffolding** - Complete absence of plugin generation/validation tooling
3. **Phase 5 Validation Layer** - Missing validation package and linting configuration

## Contract Compliance Summary

### ✅ Completed Phases (Fully or Substantially)

| Phase | Status | Evidence |
|-------|--------|----------|
| **Phase 1**: Foundation | ✅ Complete | README.md, pyproject.toml, requirements.txt, noxfile.py, core/__init__.py, .env.example, docker-compose.yml all present |
| **Phase 2**: Orchestration Core | ⚠️ Partial | core/state_machine.py, core/task_scheduler.py, core/orchestrator.py exist BUT missing schema & unit tests |
| **Phase 4**: LLM Context Broker | ✅ Complete | tools/context_broker.py, schemas/context_broker.schema.json, .context-broker.yaml present |
| **Phase 6**: Worktree Management | ✅ Complete | core/worktree/manager.py, core/worktree/sync.py, tests/test_worktree.py present |
| **Phase 7**: Observability | ✅ Complete | core/observability/tracing.py, core/observability/ledger.py, core/observability/ulid_generator.py present |
| **Phase 8**: CI/CD | ✅ Complete | .github/workflows/ with docs-guard, doc-tags, test workflows; CODEOWNERS present |
| **Phase 9**: Testing Scaffolds | ✅ Complete | tests/integration/test_workflow_execution.py, tests/conftest.py present |
| **Phase 10**: Documentation | ✅ Complete | docs/index.md, docs/OPERATING_CONTRACT.md, scripts/generate_docs.py, mkdocs.yml present |
| **Phase 11**: Deployment | ✅ Complete | core/runner.py, infrastructure/pulumi/, infrastructure/tests/test_infrastructure.py, scripts/deploy.sh present |

### ❌ Incomplete Phases (Blockers)

| Phase | Status | Missing Artifacts | Impact |
|-------|--------|-------------------|--------|
| **Phase 2**: State Machine | ⚠️ Partial | 1. `schemas/execution_state_machine.schema.json`<br>2. `tests/test_state_machine.py`<br>3. `tests/test_toposort.py` | Integration tests skip when modules aren't validated; no schema enforcement |
| **Phase 3**: Plugin System | ❌ Missing | 1. `plugins/__init__.py`<br>2. `core/Generate-PluginScaffold.ps1`<br>3. `core/Validate-Plugin.ps1`<br>4. `scripts/generate_plugin_scaffold.py`<br>5. `scripts/validate_plugin.py` | Cannot generate or validate plugins; integration tests skip plugin tests |
| **Phase 5**: Validation Layer | ❌ Missing | 1. `core/validation/code_gate.py`<br>2. `core/validation/linters.py`<br>3. `core/validation/security_scanner.py`<br>4. `.ruff.toml` | No automated quality gates; cannot route approved/rejected changes |

---

## Detailed Gap Analysis

### Gap 1: Phase 2 State Machine Governance (CRITICAL)

**Contract Requirement:**
```yaml
files:
  - schemas/execution_state_machine.schema.json
  - tests/test_state_machine.py
  - tests/test_toposort.py
```

**Current State:**
- ✅ Reference implementations exist in `/immediate CI enforcement and reproducibility/`:
  - `execution_state_machine.schema.json` ✅
  - `test_state_machine.py` ✅
  - `test_toposort.py` ✅
  - `core/state_machine.py` ✅
  - `core/task_scheduler.py` ✅

- ❌ **NOT** in the main codebase locations specified by contract:
  - Missing: `schemas/execution_state_machine.schema.json`
  - Missing: `tests/test_state_machine.py`
  - Missing: `tests/test_toposort.py`

**Impact:**
- Integration tests in `tests/integration/test_workflow_execution.py` skip tests with:
  ```python
  pytest.importorskip("core.state_machine", reason="Execution state machine module not yet implemented.")
  ```
- No JSON schema validation for state machine contracts
- No dedicated unit test coverage for state transitions and topological sorting

**Evidence from Integration Tests:**
```python
# tests/integration/test_workflow_execution.py lines 40-43
scheduler_module = pytest.importorskip(
    "core.task_scheduler", reason="Task scheduler module not yet implemented."
)
```

### Gap 2: Phase 3 Plugin System Scaffolding (CRITICAL)

**Contract Requirement:**
```yaml
files:
  - core/plugin_loader.py            ✅ EXISTS
  - plugins/__init__.py              ❌ MISSING
  - core/Generate-PluginScaffold.ps1 ❌ MISSING
  - core/Validate-Plugin.ps1         ❌ MISSING
  - scripts/generate_plugin_scaffold.py ❌ MISSING
  - scripts/validate_plugin.py       ❌ MISSING
```

**Current State:**
- ✅ Plugin loader exists: `core/plugin_loader.py`
- ❌ No `plugins/` directory scaffold
- ❌ No PowerShell generators/validators
- ❌ No Python generators/validators

**Impact:**
- Cannot generate plugin boilerplate following contract standards
- No validation mechanism for plugin.spec.json compliance
- No enforcement of plugin quality gates (coverage, linting, schema validation)
- Integration tests skip when plugins are absent

**Evidence from Build Contract:**
The contract explicitly requires plugin scaffolding tools:
```yaml
# ACMS_BUILD_EXECUTION_CONTRACT.yaml Phase 3
- {path: "core/Generate-PluginScaffold.ps1", action: create, template_id: ps_header}
- {path: "core/Validate-Plugin.ps1", action: create, template_id: ps_header}
```

**Referenced in Documentation:**
- `R_PIPELINE_IMPLEMENTATION_GUIDE.md` Section 10.1 describes `Validate-Plugin.ps1` enforcement
- `NW_DES_CHAT_FOR_NEW_ARC.md` discusses plugin validation as "Level 2" requirement

### Gap 3: Phase 5 Validation Layer (HIGH PRIORITY)

**Contract Requirement:**
```yaml
files:
  - core/validation/code_gate.py
  - core/validation/linters.py
  - core/validation/security_scanner.py
  - .ruff.toml
  - pyproject.toml (modify to add [tool.black] + [tool.mypy])
```

**Current State:**
- ❌ No `core/validation/` directory
- ❌ No code gate routing logic
- ❌ No linter integration module
- ❌ No security scanner module
- ❌ No `.ruff.toml` configuration

**Impact:**
- Cannot route changes to `.runs/approved/` vs `.runs/rejected/`
- No automated lint/test/security gates
- No integration with bandit, gitleaks, ruff, mypy, pylint
- Cannot enforce 80% coverage requirement automatically

**Evidence from Contract:**
```yaml
# ACMS_BUILD_EXECUTION_CONTRACT.yaml validation section
validation:
  coverage_min_percent: 80
  gates:
    lint: ["black","ruff","mypy","pylint"]
    test: ["pytest","pytest-testinfra"]
    security: ["bandit","gitleaks"]
  routing:
    approved_dir: ".runs/approved"
    rejected_dir: ".runs/rejected"
    retries_max: 3
```

---

## Remediation Plan

### Priority 1: Integrate Phase 2 Reference Implementations (2 hours)

**Objective:** Move reference implementations from `/immediate CI enforcement and reproducibility/` into main codebase.

#### Task 1.1: Copy Schema to Main Location
```bash
cp "immediate CI enforcement and reproducibility/execution_state_machine.schema.json" \
   schemas/execution_state_machine.schema.json
```

**Validation:**
```bash
# Validate example JSON against schema
python -m jsonschema \
  -i "immediate CI enforcement and reproducibility/execution_state_machine.example.json" \
  schemas/execution_state_machine.schema.json
```

#### Task 1.2: Copy Unit Tests to Main Location
```bash
cp "immediate CI enforcement and reproducibility/test_state_machine.py" \
   tests/test_state_machine.py

cp "immediate CI enforcement and reproducibility/test_toposort.py" \
   tests/test_toposort.py
```

**Validation:**
```bash
pytest tests/test_state_machine.py tests/test_toposort.py -v
# Expected: All tests pass
```

#### Task 1.3: Verify Integration Tests No Longer Skip
```bash
pytest tests/integration/test_workflow_execution.py -v
# Expected: Tests should now execute instead of skipping
```

**Success Criteria:**
- ✅ Schema file in correct location
- ✅ Unit tests in correct location
- ✅ All unit tests pass
- ✅ Integration tests no longer skip state machine tests
- ✅ 80%+ coverage for state machine and scheduler modules

---

### Priority 2: Implement Phase 3 Plugin System (8 hours)

**Objective:** Create plugin scaffolding and validation tooling per contract specification.

#### Task 2.1: Create Plugins Directory Structure
```bash
mkdir -p plugins
```

Create `plugins/__init__.py`:
```python
"""
ACMS Plugin Registry
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

Plugin discovery and loading for ACMS runtime.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json

__all__ = ["discover_plugins", "load_plugin"]

def discover_plugins(plugins_dir: Path = Path("plugins")) -> List[Dict[str, Any]]:
    """Discover all enabled plugins with valid plugin.spec.json."""
    discovered = []
    
    for plugin_path in plugins_dir.iterdir():
        if not plugin_path.is_dir():
            continue
            
        spec_file = plugin_path / "plugin.spec.json"
        if not spec_file.exists():
            continue
            
        try:
            with open(spec_file) as f:
                spec = json.load(f)
                
            if spec.get("enabled", False):
                discovered.append({
                    "name": spec["name"],
                    "path": plugin_path,
                    "spec": spec
                })
        except Exception:
            continue
            
    return discovered

def load_plugin(plugin_spec: Dict[str, Any]) -> Any:
    """Load plugin module by spec."""
    from core.plugin_loader import PluginLoader
    
    loader = PluginLoader(search_paths=[plugin_spec["path"]])
    return loader.load(plugin_spec["spec"]["entry_point"])
```

#### Task 2.2: Create Python Plugin Scaffold Generator
Create `scripts/generate_plugin_scaffold.py`:
```python
"""
Plugin Scaffold Generator (Python)
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

Generates plugin boilerplate following ACMS contract standards.
"""
import argparse
import json
from pathlib import Path
from datetime import date

PLUGIN_SPEC_TEMPLATE = {
    "doc_key": "PLUGIN_{NAME}",
    "semver": "1.0.0",
    "status": "active",
    "effective_date": str(date.today()),
    "owner": "Platform.Engineering",
    "contract_type": "plugin",
    "name": "",
    "version": "1.0.0",
    "enabled": True,
    "language": "python",
    "entry_point": "",
    "lifecycle_hook": "",
    "description": ""
}

HANDLER_TEMPLATE = '''"""
{name} Plugin
Version: 1.0.0
Date: {date}
Owner: Platform.Engineering
Lifecycle: {lifecycle}
"""
from typing import Dict, Any

def handle(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main plugin entry point.
    
    Args:
        input_data: Input payload with trace_id, context, etc.
        
    Returns:
        Output payload with status, results, and ledger metadata
    """
    trace_id = input_data.get("trace_id", "unknown")
    
    # TODO: Implement plugin logic
    
    return {{
        "status": "success",
        "trace_id": trace_id,
        "plugin_name": "{name}",
        "plugin_version": "1.0.0"
    }}
'''

TEST_TEMPLATE = '''"""
{name} Plugin Tests
Version: 1.0.0
Date: {date}
"""
import pytest
from {module_name} import handle

def test_handle_success():
    """Test successful plugin execution."""
    input_data = {{"trace_id": "test-123", "context": {{}}}}
    result = handle(input_data)
    
    assert result["status"] == "success"
    assert result["trace_id"] == "test-123"

def test_handle_error():
    """Test error handling."""
    # TODO: Implement error case tests
    pass
'''

def generate_scaffold(name: str, lifecycle: str, description: str, output_dir: Path):
    """Generate complete plugin scaffold."""
    plugin_dir = output_dir / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate plugin.spec.json
    spec = PLUGIN_SPEC_TEMPLATE.copy()
    spec["name"] = name
    spec["doc_key"] = f"PLUGIN_{name.upper()}"
    spec["entry_point"] = f"{name}.handle"
    spec["lifecycle_hook"] = lifecycle
    spec["description"] = description
    
    with open(plugin_dir / "plugin.spec.json", "w") as f:
        json.dump(spec, f, indent=2)
    
    # Generate handler
    handler_code = HANDLER_TEMPLATE.format(
        name=name,
        date=date.today(),
        lifecycle=lifecycle
    )
    with open(plugin_dir / f"{name}.py", "w") as f:
        f.write(handler_code)
    
    # Generate tests
    tests_dir = plugin_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").touch()
    
    test_code = TEST_TEMPLATE.format(
        name=name,
        date=date.today(),
        module_name=name
    )
    with open(tests_dir / f"test_{name}.py", "w") as f:
        f.write(test_code)
    
    # Generate empty __init__.py
    (plugin_dir / "__init__.py").touch()
    
    print(f"✅ Plugin scaffold created: {plugin_dir}")
    print(f"   - plugin.spec.json")
    print(f"   - {name}.py")
    print(f"   - tests/test_{name}.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ACMS plugin scaffold")
    parser.add_argument("--name", required=True, help="Plugin name")
    parser.add_argument("--lifecycle", required=True, help="Lifecycle hook")
    parser.add_argument("--description", required=True, help="Plugin description")
    parser.add_argument("--output-dir", default="plugins", help="Output directory")
    
    args = parser.parse_args()
    generate_scaffold(args.name, args.lifecycle, args.description, Path(args.output_dir))
```

#### Task 2.3: Create Python Plugin Validator
Create `scripts/validate_plugin.py`:
```python
"""
Plugin Validator (Python)
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

Validates plugin compliance with ACMS contract standards.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

def validate_plugin(plugin_path: Path) -> bool:
    """
    Validate plugin compliance.
    
    Returns True if all checks pass, False otherwise.
    """
    print(f"\n=== Validating Plugin: {plugin_path} ===\n")
    all_passed = True
    
    # Check 1: plugin.spec.json exists and is valid
    spec_file = plugin_path / "plugin.spec.json"
    if not spec_file.exists():
        print("✗ plugin.spec.json not found")
        return False
    
    try:
        with open(spec_file) as f:
            spec = json.load(f)
        print("✓ plugin.spec.json is valid JSON")
    except json.JSONDecodeError as e:
        print(f"✗ plugin.spec.json invalid: {e}")
        return False
    
    # Check 2: Required fields present
    required_fields = ["name", "version", "entry_point", "lifecycle_hook"]
    for field in required_fields:
        if field not in spec:
            print(f"✗ Missing required field: {field}")
            all_passed = False
        else:
            print(f"✓ Field present: {field}")
    
    # Check 3: Handler file exists
    entry_point = spec.get("entry_point", "")
    if "." in entry_point:
        module_name = entry_point.split(".")[0]
        handler_file = plugin_path / f"{module_name}.py"
        if handler_file.exists():
            print(f"✓ Handler file exists: {handler_file.name}")
        else:
            print(f"✗ Handler file not found: {handler_file.name}")
            all_passed = False
    
    # Check 4: Tests exist
    tests_dir = plugin_path / "tests"
    if tests_dir.exists() and list(tests_dir.glob("test_*.py")):
        print("✓ Tests directory exists with test files")
    else:
        print("✗ Tests directory missing or no test files")
        all_passed = False
    
    # Check 5: Run tests
    if tests_dir.exists():
        print("\nRunning tests...")
        result = subprocess.run(
            ["pytest", str(tests_dir), "-v"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ All tests passed")
        else:
            print("✗ Tests failed")
            print(result.stdout)
            all_passed = False
    
    # Check 6: Code coverage
    print("\nChecking code coverage...")
    result = subprocess.run(
        ["pytest", str(tests_dir), f"--cov={plugin_path}", "--cov-report=term-missing"],
        capture_output=True,
        text=True
    )
    
    if "TOTAL" in result.stdout:
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                parts = line.split()
                coverage = int(parts[-1].rstrip("%"))
                if coverage >= 80:
                    print(f"✓ Code coverage: {coverage}% (>= 80%)")
                else:
                    print(f"✗ Code coverage: {coverage}% (< 80%)")
                    all_passed = False
    
    # Check 7: Linting
    if spec.get("language") == "python":
        print("\nRunning linters...")
        
        # Ruff
        result = subprocess.run(
            ["ruff", "check", str(plugin_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Ruff passed")
        else:
            print("✗ Ruff found issues")
            print(result.stdout)
            all_passed = False
    
    # Final result
    print("\n=== Validation Result ===")
    if all_passed:
        print("✓ VALIDATION PASSED")
        print("Plugin is ready for deployment")
        return True
    else:
        print("✗ VALIDATION FAILED")
        print("Fix the issues above before deploying")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate ACMS plugin")
    parser.add_argument("plugin_path", help="Path to plugin directory")
    
    args = parser.parse_args()
    plugin_path = Path(args.plugin_path)
    
    if not plugin_path.is_dir():
        print(f"Error: {plugin_path} is not a directory")
        sys.exit(1)
    
    success = validate_plugin(plugin_path)
    sys.exit(0 if success else 1)
```

#### Task 2.4: Create PowerShell Scaffolding (Optional but Recommended)
Create `core/Generate-PluginScaffold.ps1`:
```powershell
<#
.SYNOPSIS
    Plugin Scaffold Generator
.VERSION
    1.0.0
.DATE
    2025-11-02
.OWNER
    Platform.Engineering
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Name,
    
    [Parameter(Mandatory=$true)]
    [string]$Lifecycle,
    
    [Parameter(Mandatory=$true)]
    [string]$Description,
    
    [string]$OutputDir = "plugins"
)

$ErrorActionPreference = "Stop"

Write-Host "Generating plugin scaffold: $Name" -ForegroundColor Cyan

# Call Python generator
python scripts/generate_plugin_scaffold.py `
    --name $Name `
    --lifecycle $Lifecycle `
    --description $Description `
    --output-dir $OutputDir

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Plugin scaffold generated successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to generate plugin scaffold" -ForegroundColor Red
    exit 1
}
```

Create `core/Validate-Plugin.ps1`:
```powershell
<#
.SYNOPSIS
    Plugin Validator
.VERSION
    1.0.0
.DATE
    2025-11-02
.OWNER
    Platform.Engineering
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PluginPath
)

$ErrorActionPreference = "Stop"

Write-Host "Validating plugin: $PluginPath" -ForegroundColor Cyan

# Call Python validator
python scripts/validate_plugin.py $PluginPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Plugin validation passed" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Plugin validation failed" -ForegroundColor Red
    exit 1
}
```

#### Task 2.5: Test Plugin System
```bash
# Generate sample plugin
python scripts/generate_plugin_scaffold.py \
  --name deduplicator \
  --lifecycle FileDetected \
  --description "Detects duplicate files by hash"

# Validate it
python scripts/validate_plugin.py plugins/deduplicator

# Expected: Validation passes
```

**Success Criteria:**
- ✅ `plugins/__init__.py` exists
- ✅ Python scaffold generator works
- ✅ Python validator works
- ✅ PowerShell wrappers work
- ✅ Can generate and validate a test plugin
- ✅ Integration tests no longer skip plugin tests

---

### Priority 3: Implement Phase 5 Validation Layer (6 hours)

**Objective:** Create validation routing and quality gate enforcement.

#### Task 3.1: Create Validation Package Structure
```bash
mkdir -p core/validation
```

Create `core/validation/__init__.py`:
```python
"""
ACMS Validation Layer
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering
"""
from .code_gate import CodeGate
from .linters import LintRunner
from .security_scanner import SecurityScanner

__all__ = ["CodeGate", "LintRunner", "SecurityScanner"]
```

#### Task 3.2: Create Code Gate Router
Create `core/validation/code_gate.py`:
```python
"""
Code Gate — Validation Router
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

Routes approved/rejected changes by quality gates.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import shutil

class CodeGate:
    """Routes changes based on validation results."""
    
    def __init__(
        self,
        approved_dir: Path = Path(".runs/approved"),
        rejected_dir: Path = Path(".runs/rejected"),
        max_retries: int = 3
    ):
        self.approved_dir = approved_dir
        self.rejected_dir = rejected_dir
        self.max_retries = max_retries
        
        # Ensure directories exist
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)
    
    def route(
        self,
        change_id: str,
        validation_results: Dict[str, Any],
        source_path: Path
    ) -> Dict[str, Any]:
        """
        Route change to approved or rejected directory.
        
        Args:
            change_id: Unique identifier for this change
            validation_results: Results from all gates
            source_path: Path to change artifact
            
        Returns:
            Routing decision with destination path
        """
        all_passed = all(
            result.get("passed", False)
            for result in validation_results.values()
        )
        
        if all_passed:
            dest_dir = self.approved_dir / change_id
            status = "approved"
        else:
            attempt = validation_results.get("attempt", 1)
            if attempt >= self.max_retries:
                dest_dir = self.rejected_dir / change_id
                status = "rejected"
            else:
                # Allow retry
                return {
                    "status": "retry",
                    "attempt": attempt + 1,
                    "failures": [
                        gate for gate, result in validation_results.items()
                        if not result.get("passed", False)
                    ]
                }
        
        # Copy to destination
        dest_dir.mkdir(parents=True, exist_ok=True)
        if source_path.is_file():
            shutil.copy2(source_path, dest_dir / source_path.name)
        else:
            shutil.copytree(source_path, dest_dir, dirs_exist_ok=True)
        
        return {
            "status": status,
            "destination": str(dest_dir),
            "validation_results": validation_results
        }
```

#### Task 3.3: Create Linter Integration
Create `core/validation/linters.py`:
```python
"""
Linting Integration
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

Integrates Black/Ruff/mypy/pylint.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Dict, Any, List

class LintRunner:
    """Runs linting tools on code."""
    
    def __init__(self, tools: List[str] = None):
        self.tools = tools or ["ruff", "black", "mypy", "pylint"]
    
    def run(self, target_path: Path) -> Dict[str, Any]:
        """
        Run all configured linters.
        
        Args:
            target_path: Path to lint
            
        Returns:
            Results from all linters
        """
        results = {
            "passed": True,
            "tools": {}
        }
        
        for tool in self.tools:
            tool_result = self._run_tool(tool, target_path)
            results["tools"][tool] = tool_result
            if not tool_result["passed"]:
                results["passed"] = False
        
        return results
    
    def _run_tool(self, tool: str, target_path: Path) -> Dict[str, Any]:
        """Run individual linting tool."""
        if tool == "ruff":
            cmd = ["ruff", "check", str(target_path)]
        elif tool == "black":
            cmd = ["black", "--check", str(target_path)]
        elif tool == "mypy":
            cmd = ["mypy", str(target_path)]
        elif tool == "pylint":
            cmd = ["pylint", str(target_path)]
        else:
            return {"passed": False, "error": f"Unknown tool: {tool}"}
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "error": "Timeout"
            }
        except FileNotFoundError:
            return {
                "passed": False,
                "error": f"Tool not installed: {tool}"
            }
```

#### Task 3.4: Create Security Scanner
Create `core/validation/security_scanner.py`:
```python
"""
Security Scanning
Version: 1.0.0
Date: 2025-11-02
Owner: Platform.Engineering

Integrates bandit + gitleaks.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Dict, Any

class SecurityScanner:
    """Runs security scanning tools."""
    
    def run(self, target_path: Path) -> Dict[str, Any]:
        """
        Run security scans.
        
        Args:
            target_path: Path to scan
            
        Returns:
            Security scan results
        """
        results = {
            "passed": True,
            "scans": {}
        }
        
        # Run bandit (Python security)
        bandit_result = self._run_bandit(target_path)
        results["scans"]["bandit"] = bandit_result
        if not bandit_result["passed"]:
            results["passed"] = False
        
        # Run gitleaks (secrets detection)
        gitleaks_result = self._run_gitleaks(target_path)
        results["scans"]["gitleaks"] = gitleaks_result
        if not gitleaks_result["passed"]:
            results["passed"] = False
        
        return results
    
    def _run_bandit(self, target_path: Path) -> Dict[str, Any]:
        """Run bandit security scanner."""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(target_path), "-f", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Bandit returns 1 if issues found
            return {
                "passed": result.returncode == 0,
                "output": result.stdout
            }
        except FileNotFoundError:
            return {
                "passed": False,
                "error": "Bandit not installed"
            }
    
    def _run_gitleaks(self, target_path: Path) -> Dict[str, Any]:
        """Run gitleaks secrets scanner."""
        try:
            result = subprocess.run(
                ["gitleaks", "detect", "--source", str(target_path), "--no-git"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "passed": result.returncode == 0,
                "output": result.stdout
            }
        except FileNotFoundError:
            return {
                "passed": False,
                "error": "Gitleaks not installed"
            }
```

#### Task 3.5: Create Ruff Configuration
Create `.ruff.toml`:
```toml
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Platform.Engineering
# Version: 1.0.0
# Last Modified: 2025-11-02

target-version = "py311"
line-length = 100

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "T10", # flake8-debugger
    "ISC", # flake8-implicit-str-concat
    "ICN", # flake8-import-conventions
    "PIE", # flake8-pie
    "PT",  # flake8-pytest-style
    "Q",   # flake8-quotes
    "RET", # flake8-return
    "SIM", # flake8-simplify
    "TID", # flake8-tidy-imports
    "ARG", # flake8-unused-arguments
    "PTH", # flake8-use-pathlib
]

ignore = [
    "E501",  # line too long (handled by black)
]

[lint.per-file-ignores]
"tests/**/*.py" = ["ARG"]

[format]
quote-style = "double"
indent-style = "space"
```

#### Task 3.6: Update pyproject.toml
Add to `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### Task 3.7: Create Validation Integration Test
Create `tests/test_validation_gate.py`:
```python
"""
Validation Gate Integration Tests
Version: 1.0.0
Date: 2025-11-02
"""
import pytest
from pathlib import Path
from core.validation import CodeGate, LintRunner, SecurityScanner

def test_code_gate_routes_approved(tmp_path):
    """Test that passing validation routes to approved directory."""
    gate = CodeGate(
        approved_dir=tmp_path / "approved",
        rejected_dir=tmp_path / "rejected"
    )
    
    validation_results = {
        "lint": {"passed": True},
        "security": {"passed": True},
        "tests": {"passed": True}
    }
    
    source = tmp_path / "change.py"
    source.write_text("# Valid code\n")
    
    result = gate.route("change-001", validation_results, source)
    
    assert result["status"] == "approved"
    assert (tmp_path / "approved" / "change-001").exists()

def test_code_gate_routes_rejected(tmp_path):
    """Test that failing validation routes to rejected directory."""
    gate = CodeGate(
        approved_dir=tmp_path / "approved",
        rejected_dir=tmp_path / "rejected",
        max_retries=1
    )
    
    validation_results = {
        "lint": {"passed": False},
        "security": {"passed": True},
        "tests": {"passed": True},
        "attempt": 1
    }
    
    source = tmp_path / "change.py"
    source.write_text("# Invalid code\n")
    
    result = gate.route("change-002", validation_results, source)
    
    assert result["status"] == "rejected"
    assert (tmp_path / "rejected" / "change-002").exists()
```

**Success Criteria:**
- ✅ `core/validation/` package exists
- ✅ Code gate routes changes correctly
- ✅ Linter integration works
- ✅ Security scanner works
- ✅ `.ruff.toml` configuration present
- ✅ Validation tests pass

---

## Verification Checklist

After completing all remediation tasks, verify full compliance:

### Phase 2 Verification
- [ ] `schemas/execution_state_machine.schema.json` exists
- [ ] Schema validates example JSON successfully
- [ ] `tests/test_state_machine.py` exists and passes
- [ ] `tests/test_toposort.py` exists and passes
- [ ] Integration tests no longer skip state machine tests
- [ ] Coverage >= 80% for state machine module

### Phase 3 Verification
- [ ] `plugins/__init__.py` exists
- [ ] `scripts/generate_plugin_scaffold.py` works
- [ ] `scripts/validate_plugin.py` works
- [ ] `core/Generate-PluginScaffold.ps1` works
- [ ] `core/Validate-Plugin.ps1` works
- [ ] Can generate and validate a test plugin successfully
- [ ] Integration tests no longer skip plugin tests

### Phase 5 Verification
- [ ] `core/validation/__init__.py` exists
- [ ] `core/validation/code_gate.py` exists and routes correctly
- [ ] `core/validation/linters.py` exists and runs tools
- [ ] `core/validation/security_scanner.py` exists and scans
- [ ] `.ruff.toml` exists and is valid
- [ ] `pyproject.toml` has [tool.black] and [tool.mypy] sections
- [ ] Validation integration tests pass

### Full System Verification
```bash
# Run all tests
pytest tests/ -v --cov=core --cov=plugins

# Expected:
# - All tests pass
# - Coverage >= 80%
# - No tests skipped due to missing modules

# Run all linters
ruff check .
black --check .
mypy core/

# Run CI pipeline locally
nox

# Expected: All sessions pass
```

---

## Timeline Estimate

| Priority | Tasks | Estimated Time | Dependencies |
|----------|-------|---------------|--------------|
| Priority 1 | Phase 2 State Machine | 2 hours | Reference implementations |
| Priority 2 | Phase 3 Plugin System | 8 hours | Phase 2 complete |
| Priority 3 | Phase 5 Validation Layer | 6 hours | Phase 2, 3 complete |
| **Total** | | **16 hours** | |

---

## Risk Mitigation

### Risk 1: Reference Implementation Mismatch
**Mitigation:** The reference implementations in `/immediate CI enforcement and reproducibility/` are already battle-tested. Copy them as-is, then extend incrementally.

### Risk 2: Integration Test Failures
**Mitigation:** Integration tests use `pytest.importorskip()` which will fail gracefully. Fix imports progressively.

### Risk 3: Plugin System Complexity
**Mitigation:** Start with minimal Python implementation. PowerShell wrappers are optional and can be added later.

---

## Success Metrics

Upon completion:
- ✅ Zero integration tests skipping due to missing modules
- ✅ 58/58 files from Build Execution Contract present
- ✅ 80%+ test coverage across all modules
- ✅ All CI/CD checks passing
- ✅ Full contract compliance achieved

---

## Next Steps After Remediation

1. **Phase 12: Advanced Features** (Future)
   - Add parallel execution support
   - Implement resource quotas
   - Add observability dashboards

2. **Phase 13: Production Hardening**
   - Load testing
   - Chaos engineering
   - Disaster recovery drills

3. **Phase 14: Developer Experience**
   - VSCode extensions
   - CLI tooling
   - Interactive documentation

---

*Gap Analysis v1.0.0*  
*Last Updated: 2025-11-02*  
*Document Owner: Platform.Engineering*  
*Next Review: Upon completion of remediation*
