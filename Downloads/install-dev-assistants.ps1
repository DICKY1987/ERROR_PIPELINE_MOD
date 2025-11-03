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
#   - LangGraph CLI        (LangGraph local dev tooling / orchestration CLI)
#   - Uvicorn              (ASGI server runtime)
#   - FastAPI (pipx inject into uvicorn environment)
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
#        .\install-dev-assistants.ps1
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

    # Check if already installed
    $already = winget list --id $Id --source winget 2>$null | Select-String $Id
    if ($already) {
        Write-Host "   - already installed, skipping."
        return
    }

    $cmd = "winget install --id $Id -e --accept-package-agreements --accept-source-agreements $ExtraArgs"
    Write-Host "   - running: $cmd"
    iex $cmd
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

# -- REQUIRED LIST PER REQUEST --
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
# Specify CLI via uv "tool install". Assumes uv is now on PATH.
# NOTE: if this fails because uv isn't in PATH yet, open a new terminal and run this block manually.
try {
    & uv tool install specify-cli --from git+https://github.com/github/spec-kit.git --force
} catch {
    Write-Warning "specify-cli install via uv failed: $($_.Exception.Message)"
    Write-Warning "Retry manually after opening a new terminal:"
    Write-Warning "    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git --force"
}

Write-Section "5. Install OpenAI Codex CLI (Node.js / npm)"
# Codex CLI (experimental on Windows). Requires Node.js LTS from above.
try {
    npm install -g @openai/codex
} catch {
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

# Pre-pull DeepSeek model (this may take time/download)
try {
    & ollama pull deepseek-coder-v2:lite
} catch {
    Write-Warning "ollama pull deepseek-coder-v2:lite failed: $($_.Exception.Message)"
    Write-Warning "If Ollama service isn't running yet, start Ollama Desktop or 'ollama serve' and retry:"
    Write-Warning "    ollama pull deepseek-coder-v2:lite"
}

Write-Section "7. Versions / sanity check"
Write-Host "Python:"    (& $PythonCmd --version)
Write-Host "pipx:"      (& $PythonCmd -m pipx --version)
Write-Host "nox:"       (nox --version 2>$null)
Write-Host "aider:"     (aider --version 2>$null)
Write-Host "langgraph:" (langgraph --version 2>$null)
Write-Host "uvicorn:"   (uvicorn --version 2>$null)
Write-Host "fastapi:"   (& $PythonCmd -m pipx runpip uvicorn show fastapi 2>$null | Select-String Version)
Write-Host "uv:"        (uv --version 2>$null)
Write-Host "specify:"   (specify --version 2>$null)
Write-Host "node:"      (node -v 2>$null)
Write-Host "npm:"       (npm -v 2>$null)
Write-Host "codex:"     (codex --version 2>$null)
Write-Host "ollama:"    (ollama --version 2>$null)

Write-Host "`nAll done. Open a NEW PowerShell window to ensure PATH and env vars are loaded." -ForegroundColor Green
# =====================================================================
