<# =====================================================================
 Invoke-Build Orchestrator for Dev Assistants / Local AI Tooling
 - Deterministic tasks with Inputs/Outputs (incremental)
 - Strict error handling (terminating errors)
 - Cross-platform friendly structure (Windows focus with guards)
 - Parallel-ready tasks (independent installs can run concurrently)
 - Handles Windows-specific caveats found in the report

 REQUIREMENTS:
   - PowerShell 7+ (pwsh)
   - InvokeBuild module:  Install-Module InvokeBuild -Scope CurrentUser
   - On Windows, run in elevated shell for winget-based tasks

 USAGE (local):
   pwsh -NoLogo -ExecutionPolicy Bypass -File .\build.ps1 Install
   # or a subset:
   pwsh -File .\build.ps1 Pipx.Tools

 CI/CD:
   - Use 'pwsh' shell and call 'ib' wrapper (if installed) or 'Invoke-Build' directly.

 NOTES:
   - Marker files under .state\ are used as Outputs to make tasks incremental.
   - Set -CodexOptIn:$true to install experimental Codex CLI on Windows.
===================================================================== #>

param(
  [switch]$CodexOptIn = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Ensure a local state directory for marker files
$StateDir = Join-Path $PSScriptRoot '.state'
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

# Helper: write a marker file on success
function Set-Marker {
  param([Parameter(Mandatory=$true)][string]$Name)
  $path = Join-Path $StateDir $Name
  New-Item -ItemType File -Force -Path $path | Out-Null
  return $path
}

# Helper: safe winget install
function Invoke-WingetInstall {
  param(
    [Parameter(Mandatory)][string]$Id,
    [Parameter(Mandatory)][string]$Desc,
    [string]$ExtraArgs = ''
  )
  Write-Host ">> $Desc ($Id)" -ForegroundColor Cyan
  $listed = winget list --id $Id --exact 2>$null
  if (($LASTEXITCODE -eq 0) -and ($listed | Select-String -SimpleMatch $Id)) {
    Write-Host "   - already installed, skipping."
    return
  }
  $args = @('install','--id',$Id,'-e','--accept-package-agreements','--accept-source-agreements')
  if ($ExtraArgs) { $args += $ExtraArgs.Split(' ') }
  Write-Host "   - winget $($args -join ' ')"
  & winget @args
}

# Helper: ensure pipx available
function Ensure-Pipx {
  $py = Get-Command py.exe,python.exe,python3.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $py) { throw "Python not found in PATH after install." }
  & $($py.Source) -m pip install --user --upgrade pip pipx | Out-Null
  & $($py.Source) -m pipx ensurepath | Out-Null
  # Refresh PATH in-session
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
              [System.Environment]::GetEnvironmentVariable('Path','User')
}

# Helper: pipx install wrapper
function Invoke-PipxInstall {
  param(
    [Parameter(Mandatory)][string]$Package,
    [string[]]$Args
  )
  $py = Get-Command py.exe,python.exe,python3.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $py) { throw "Python not found for pipx." }
  & $($py.Source) -m pipx install $Package --force @Args
}

# Helper: pipx inject wrapper
function Invoke-PipxInject {
  param(
    [Parameter(Mandatory)][string]$Target,
    [Parameter(Mandatory)][string[]]$Deps
  )
  $py = Get-Command py.exe,python.exe,python3.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $py) { throw "Python not found for pipx inject." }
  & $($py.Source) -m pipx inject $Target @Deps
}

# ---- Tasks ----
# Root
task Install Init, Winget.Core, Pipx.Tools, Specify, Codex?, Ollama.Config, Verify

# Guards and prep
task Init {
  if ($IsWindows -and -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run elevated on Windows for winget-based tasks."
  }
  if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "PowerShell 7+ required."
  }
}

# Core runtimes via winget
task Winget.Core Winget.Python, Winget.UV, Winget.Node, Winget.Ollama

task Winget.Python -Inputs {} -Outputs { Join-Path $StateDir 'python-3.12.ok' } {
  Invoke-WingetInstall -Id 'Python.Python.3.12' -Desc 'Python 3.12 runtime'
  Set-Marker 'python-3.12.ok' | Out-Null
}

task Winget.UV -Inputs {} -Outputs { Join-Path $StateDir 'uv.ok' } {
  Invoke-WingetInstall -Id 'astral-sh.uv' -Desc 'uv package manager'
  Set-Marker 'uv.ok' | Out-Null
}

task Winget.Node -Inputs {} -Outputs { Join-Path $StateDir 'node-lts.ok' } {
  Invoke-WingetInstall -Id 'OpenJS.NodeJS.LTS' -Desc 'Node.js LTS (with npm)' -ExtraArgs '--scope machine'
  Set-Marker 'node-lts.ok' | Out-Null
}

task Winget.Ollama -Inputs {} -Outputs { Join-Path $StateDir 'ollama.ok' } {
  Invoke-WingetInstall -Id 'Ollama.Ollama' -Desc 'Ollama local LLM runtime'
  Write-Host "NOTE: If the installer 'hangs', close Overwolf from tray; installer then completes." -ForegroundColor DarkYellow
  Set-Marker 'ollama.ok' | Out-Null
}

# pipx tools
task Pipx.Tools Pipx.Init, Pipx.Nox, Pipx.Aider, Pipx.LangGraph, Pipx.Uvicorn, Pipx.FastAPI

task Pipx.Init -Inputs { Join-Path $StateDir 'python-3.12.ok' } -Outputs { Join-Path $StateDir 'pipx.ok' } {
  Ensure-Pipx
  Set-Marker 'pipx.ok' | Out-Null
}

task Pipx.Nox -Inputs { Join-Path $StateDir 'pipx.ok' } -Outputs { Join-Path $StateDir 'nox.ok' } {
  Invoke-PipxInstall -Package 'nox'
  Set-Marker 'nox.ok' | Out-Null
}

task Pipx.Aider -Inputs { Join-Path $StateDir 'pipx.ok' } -Outputs { Join-Path $StateDir 'aider.ok' } {
  Invoke-PipxInstall -Package 'aider-chat'
  Set-Marker 'aider.ok' | Out-Null
}

# Pin langgraph-cli to 0.0.14 (>=0.0.15 broken on Windows)
task Pipx.LangGraph -Inputs { Join-Path $StateDir 'pipx.ok' } -Outputs { Join-Path $StateDir 'langgraph.ok' } {
  Invoke-PipxInstall -Package 'langgraph-cli==0.0.14'
  Set-Marker 'langgraph.ok' | Out-Null
}

task Pipx.Uvicorn -Inputs { Join-Path $StateDir 'pipx.ok' } -Outputs { Join-Path $StateDir 'uvicorn.ok' } {
  Invoke-PipxInstall -Package 'uvicorn'
  Set-Marker 'uvicorn.ok' | Out-Null
}

task Pipx.FastAPI -Inputs { Join-Path $StateDir 'uvicorn.ok' } -Outputs { Join-Path $StateDir 'fastapi.injected.ok' } {
  Invoke-PipxInject -Target 'uvicorn' -Deps @('fastapi')
  Set-Marker 'fastapi.injected.ok' | Out-Null
}

# Specify CLI via uv (with fallback syntax)
task Specify -Inputs { Join-Path $StateDir 'uv.ok' } -Outputs { Join-Path $StateDir 'specify.ok' } {
  $ok = $false
  try {
    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git --force
    $ok = $true
  } catch {
    Write-Warning "specify-cli '--from' failed: $($_.Exception.Message)"
    try {
      uv tool install git+https://github.com/github/spec-kit.git#specify-cli --force
      $ok = $true
    } catch {
      Write-Warning "specify-cli fallback failed: $($_.Exception.Message)"
    }
  }
  if (-not $ok) { throw "Specify CLI install failed. Try a new terminal to refresh PATH, then rerun 'Invoke-Build Specify'." }
  Set-Marker 'specify.ok' | Out-Null
}

# Optional: Codex CLI (experimental on Windows). Controlled by -CodexOptIn switch.
task Codex? -If { $CodexOptIn } -Inputs { Join-Path $StateDir 'node-lts.ok' } -Outputs { Join-Path $StateDir 'codex.ok' } {
  Write-Host "Installing Codex CLI (experimental on Windows). WSL recommended if this fails." -ForegroundColor DarkYellow
  npm install -g @openai/codex
  Set-Marker 'codex.ok' | Out-Null
}

# Ollama config + DeepSeek model pre-pull
task Ollama.Config -Inputs { Join-Path $StateDir 'ollama.ok' } -Outputs { Join-Path $StateDir 'ollama.deepseek.ok' } {
  $env:OLLAMA_API_BASE = 'http://127.0.0.1:11434'
  setx OLLAMA_API_BASE $env:OLLAMA_API_BASE | Out-Null
  try {
    ollama pull deepseek-coder-v2:lite
  } catch {
    Write-Warning "ollama pull failed: $($_.Exception.Message). Start 'ollama serve' or Ollama Desktop, then 'Invoke-Build Ollama.Config'."
  }
  Set-Marker 'ollama.deepseek.ok' | Out-Null
}

# Verify / versions
task Verify {
  function Show($name, $cmd) {
    try {
      $v = & $cmd 2>$null
      if ($v) { Write-Host ("{0}: {1}" -f $name, ($v | Out-String).Trim()) }
      else { Write-Host ("{0}: <not found>" -f $name) -ForegroundColor DarkYellow }
    } catch {
      Write-Host ("{0}: <error> {1}" -f $name, $_.Exception.Message) -ForegroundColor Red
    }
  }

  $py = (Get-Command py.exe,python.exe,python3.exe -ErrorAction SilentlyContinue | Select-Object -First 1).Source
  if ($py) {
    Show 'Python' { & $py --version }
    Show 'pipx'   { & $py -m pipx --version }
    Show 'fastapi in uvicorn venv' { & $py -m pipx runpip uvicorn show fastapi | Select-String Version }
  } else {
    Write-Host "Python: <not found>" -ForegroundColor DarkYellow
  }

  Show 'nox'       { nox --version }
  Show 'aider'     { aider --version }
  Show 'langgraph' { langgraph --version }
  Show 'uvicorn'   { uvicorn --version }
  Show 'uv'        { uv --version }
  Show 'specify'   { specify --version }
  Show 'node'      { node -v }
  Show 'npm'       { npm -v }
  Show 'codex'     { codex --version }
  Show 'ollama'    { ollama --version }
}
