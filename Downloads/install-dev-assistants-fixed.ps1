# =====================================================================
# DEV ASSISTANTS / LOCAL AI TOOLING INSTALLER (Windows 11+)
#
# Installs via winget:
#   - Python 3.x        (runtime for pipx tools)
#   - uv                (fast Python tool/package manager, used for Specify CLI)
#   - Node.js LTS       (runtime for npm / Codex CLI)
#   - Ollama            (local LLM runtime for DeepSeek)
#
# Installs via pipx (isolated Python CLIs):
#   - Nox                  (automation / test session runner)
#   - Aider                (AI pair programmer with Git awareness)
#   - LangGraph CLI        (LangGraph local dev/orchestration CLI)
#   - Uvicorn              (ASGI server runtime)
#   - FastAPI              (injected into Uvicorn's pipx venv)
#
# Also installs:
#   - Specify CLI          (via uv tool install)
#   - Codex CLI            (via npm, requires Node.js LTS)
#
# After install:
#   - Sets OLLAMA_API_BASE for aider
#   - Pre-pulls deepseek-coder-v2:lite for Ollama so aider won't stall
#
# Usage:
#   1. Open PowerShell 7+ *as Administrator*
#   2. Run:
#        Set-ExecutionPolicy Bypass -Scope Process -Force;
#        .\install-dev-assistants-fixed.ps1
#
# NOTE:
#   Script is idempotent-ish: if something is already installed, winget will skip,
#   and pipx installs are called with --force to ensure they're present/updated.
# =====================================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

# ------------------ helper functions ------------------

function Write-Section {
    param([string]$Msg)
    Write-Host ""
    Write-Host "=== $Msg ===" -ForegroundColor Cyan
}

function Ensure-Admin {
    $isAdmin = ([Security.Principal.WindowsPrincipal] `
        [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        throw "Please run this script in an ELEVATED PowerShell (Run as Administrator)."
    }
}

function Refresh-EnvPath {
    # Pull fresh Machine+User PATH into this session
    $machine = [System.Environment]::GetEnvironmentVariable('Path','Machine')
    $user    = [System.Environment]::GetEnvironmentVariable('Path','User')
    $env:Path = ($machine + ';' + $user)
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory=$true)][string]$Id,
        [Parameter(Mandatory=$true)][string]$Desc,
        [string]$ExtraArgs = ""
    )

    Write-Host ">> $Desc ($Id)"

    # More robust "already installed" check:
    $listed = winget list --id $Id --exact 2>$null
    if (($LASTEXITCODE -eq 0) -and ($listed | Select-String -SimpleMatch $Id)) {
        Write-Host "   - already installed, skipping."
        return
    }

    $args = @(
        "install",
        "--id", $Id,
        "-e",
        "--accept-package-agreements",
        "--accept-source-agreements"
    )

    if ($ExtraArgs) {
        # allow caller to pass things like "--scope machine"
        $args += $ExtraArgs.Split(' ')
    }

    Write-Host "   - running: winget $($args -join ' ')"
    & winget @args
}

function Get-PythonCmd {
    # Returns best Python launcher we can find after install
    $candidates = @("py.exe","python.exe","python3.exe")
    foreach ($c in $candidates) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Path }
    }
    throw "Python executable not found in PATH. Open a new terminal and re-run, or ensure Python is installed."
}

function Ensure-Pipx {
    param([string]$PythonCmd)

    Write-Host ">> Ensuring pipx is installed & on PATH"

    # Upgrade pip + install/upgrade pipx for current user
    & $PythonCmd -m pip install --user --upgrade pip pipx | Out-Null

    # Make sure pipx puts shims in ~/.local/bin and PATH knows about it
    & $PythonCmd -m pipx ensurepath | Out-Null

    # refresh env for this session so we can call pipx later
    Refresh-EnvPath
}

function Pipx-Install {
    param(
        [string]$PythonCmd,
        [Parameter(Mandatory=$true)][string]$PackageName,
        [string[]]$ExtraArgs
    )

    Write-Host "   - pipx install $PackageName"
    & $PythonCmd -m pipx install $PackageName --force @ExtraArgs
}

function Pipx-Inject {
    param(
        [string]$PythonCmd,
        [Parameter(Mandatory=$true)][string]$Target,
        [Parameter(Mandatory=$true)][string[]]$Deps
    )
    Write-Host "   - pipx inject $Target $($Deps -join ' ')"
    & $PythonCmd -m pipx inject $Target $Deps
}

# ------------------ main flow ------------------

Ensure-Admin
Write-Section "1. Install core runtimes via winget (Python, uv, Node.js LTS, Ollama)"

# Python (pin to 3.12.* for stability; adjust if you prefer a different minor)
Install-WingetPackage -Id "Python.Python.3.12" -Desc "Python 3.x runtime (winget)"
Refresh-EnvPath

# uv (fast Python package/project manager; needed for Specify CLI install)
Install-WingetPackage -Id "astral-sh.uv" -Desc "uv package manager"
Refresh-EnvPath

# Node.js LTS (required for npm global install of Codex CLI)
Install-WingetPackage -Id "OpenJS.NodeJS.LTS" -Desc "Node.js LTS (with npm)" -ExtraArgs "--scope machine"
Refresh-EnvPath

# Ollama (local LLM runtime/server used by Aider to run deepseek locally)
Install-WingetPackage -Id "Ollama.Ollama" -Desc "Ollama local LLM runtime"
Refresh-EnvPath

Write-Section "2. Set up pipx so Python CLIs are isolated"
$PythonCmd = Get-PythonCmd
Ensure-Pipx -PythonCmd $PythonCmd

Write-Section "3. Install Python developer CLIs with pipx"

# -- REQUIRED LIST --
# - Nox (pipx)
# - Aider (pipx)
# - LangGraph CLI (pipx)
# - Uvicorn (pipx)
# - FastAPI (pipx inject into uvicorn env)

# 3a. Nox (automation / test session runner)
Pipx-Install -PythonCmd $PythonCmd -PackageName "nox"

# 3b. Aider (AI pair programmer w/ git awareness)
Pipx-Install -PythonCmd $PythonCmd -PackageName "aider-chat"

# 3c. LangGraph CLI (LangGraph local dev/orchestration CLI)
Pipx-Install -PythonCmd $PythonCmd -PackageName "langgraph-cli"

# 3d. Uvicorn (ASGI server runtime)
Pipx-Install -PythonCmd $PythonCmd -PackageName "uvicorn"

# 3e. Inject FastAPI into Uvicorn's isolated pipx venv
Pipx-Inject -PythonCmd $PythonCmd -Target "uvicorn" -Deps @("fastapi")

Write-Section "4. Install Specify CLI using uv"
# We'll attempt the documented form first, then fall back to alt syntax if that fails.
try {
    & uv tool install specify-cli --from git+https://github.com/github/spec-kit.git --force
}
catch {
    Write-Warning "specify-cli install with '--from' form failed: $($_.Exception.Message)"
    Write-Warning "Trying fallback form with fragment syntax..."
    try {
        & uv tool install git+https://github.com/github/spec-kit.git#specify-cli --force
    }
    catch {
        Write-Warning "Fallback Specify CLI install also failed: $($_.Exception.Message)"
        Write-Warning "You may need to open a NEW terminal so PATH includes uv, then run manually."
    }
}

Write-Section "5. Install OpenAI Codex CLI (Node.js / npm)"
# Codex CLI (experimental on Windows). Requires Node.js LTS from above.
try {
    npm install -g @openai/codex
}
catch {
    Write-Warning "Codex CLI npm install failed: $($_.Exception.Message)"
    Write-Warning "You may need to re-open PowerShell or run in WSL."
}

Write-Section "6. Configure Ollama + DeepSeek model for Aider"
# Make Aider happy:
# - Tell Aider where local Ollama API lives
# - Pre-pull the deepseek-coder-v2:lite model so Aider won't stall the first time

$ollamaBase = "http://127.0.0.1:11434"
$env:OLLAMA_API_BASE = $ollamaBase
setx OLLAMA_API_BASE $ollamaBase | Out-Null

# Pre-pull DeepSeek model
try {
    & ollama pull deepseek-coder-v2:lite
}
catch {
    Write-Warning "ollama pull deepseek-coder-v2:lite failed: $($_.Exception.Message)"
    Write-Warning "If Ollama service isn't running yet, start Ollama Desktop or 'ollama serve' and retry:"
    Write-Warning "    ollama pull deepseek-coder-v2:lite"
}

Write-Section "7. Versions / sanity check"
try {
    Write-Host ("Python: {0}"    -f (& $PythonCmd --version 2>$null))
} catch { Write-Host ("Python: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("pipx: {0}"      -f (& $PythonCmd -m pipx --version 2>$null))
} catch { Write-Host ("pipx: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("nox: {0}"       -f (nox --version 2>$null))
} catch { Write-Host ("nox: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("aider: {0}"     -f (aider --version 2>$null))
} catch { Write-Host ("aider: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("langgraph: {0}" -f (langgraph --version 2>$null))
} catch { Write-Host ("langgraph: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("uvicorn: {0}"   -f (uvicorn --version 2>$null))
} catch { Write-Host ("uvicorn: <error> {0}" -f $_.Exception.Message) }

try {
    $fastapiVer = & $PythonCmd -m pipx runpip uvicorn show fastapi 2>$null | Select-String Version
    Write-Host ("fastapi: {0}"  -f ($fastapiVer | ForEach-Object { $_.ToString().Trim() } ))
} catch { Write-Host ("fastapi: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("uv: {0}"        -f (uv --version 2>$null))
} catch { Write-Host ("uv: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("specify: {0}"   -f (specify --version 2>$null))
} catch { Write-Host ("specify: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("node: {0}"      -f (node -v 2>$null))
} catch { Write-Host ("node: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("npm: {0}"       -f (npm -v 2>$null))
} catch { Write-Host ("npm: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("codex: {0}"     -f (codex --version 2>$null))
} catch { Write-Host ("codex: <error> {0}" -f $_.Exception.Message) }

try {
    Write-Host ("ollama: {0}"    -f (ollama --version 2>$null))
} catch { Write-Host ("ollama: <error> {0}" -f $_.Exception.Message) }

Write-Host "`nAll done. Open a NEW PowerShell window to ensure PATH and env vars are loaded." -ForegroundColor Green
# =====================================================================
