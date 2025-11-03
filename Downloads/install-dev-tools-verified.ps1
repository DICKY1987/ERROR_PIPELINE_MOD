# =====================================================================
# CLI STACK INSTALLER (Windows 11+) - VERIFIED PACKAGES ONLY
# Idempotent • Skip-on-failure • Version pins • Offline cache • JSON/CSV report
# =====================================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# ---------------- CONFIG ----------------
$PINNED = $true
$CACHE = @{
    enabled = $false
    prefetch = $false
    use_only = $false
    root = "C:\dev-cache"
    npm_dir = $null
    wheel_dir = $null
    choco_dir = $null
}

$VERS = @{
    winget = @{
        'Git.Git' = ''
        'Git.GitLFS' = ''
        'GitHub.cli' = ''
        'OpenJS.NodeJS.LTS' = ''
        'Python.Python.3.12' = ''
        'Microsoft.PowerShell' = ''
        'Microsoft.VisualStudioCode' = ''
        '7zip.7zip' = ''
        'jqlang.jq' = ''
        'MikeFarah.yq' = ''
        'BurntSushi.ripgrep.MSVC' = ''
        'sharkdp.fd' = ''
        'Task.Task' = ''
        'AquaSecurity.Trivy' = ''
        'Ollama.Ollama' = ''
        'PostgreSQL.PostgreSQL' = ''
        'tporadowski.redis' = ''
    }
    choco = @{
        'make' = ''
        'go-task' = ''
    }
    npm = @{
        '@anthropic-ai/claude-code' = ''
        '@google/gemini-cli' = ''
        'openai' = ''
        '@github/copilot' = ''
        'prettier' = ''
        'eslint' = ''
        'pyright' = ''
        'markdownlint-cli' = ''
        'pnpm' = ''
    }
    pipx = @{
        'ruff' = ''
        'black' = ''
        'isort' = ''
        'pylint' = ''
        'mypy' = ''
        'bandit' = ''
        'safety' = ''
        'semgrep' = ''
        'yamllint' = ''
        'mdformat' = ''
        'codespell' = ''
        'pytest' = ''
    }
}

$WINGET_TO_CHOCO = @{
    'Task.Task' = 'go-task'
}

# ---------------- internals ----------------
$results = New-Object System.Collections.Generic.List[object]

function Now {
    Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
}

function Log($level, $name, $msg) {
    $color = switch ($level) {
        'OK' { 'Green' }
        'SKIP' { 'DarkYellow' }
        'ERR' { 'Red' }
        default { 'Gray' }
    }
    Write-Host ("[{0}] [{1}] {2} - {3}" -f (Now), $level, $name, $msg) -ForegroundColor $color
}

function AddResult($name, $ok, $details, $src = '', $version = '') {
    $results.Add([pscustomobject]@{
            name    = $name
            ok      = $ok
            details = $details
            source  = $src
            version = $version
        })
}

function Ensure-Admin {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Please run this script in an **elevated** PowerShell (Run as Administrator)."
    }
}

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Test-Cmd($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Wait-ForCommand($cmd, $seconds = 45) {
    for ($i = 0; $i -lt $seconds; $i++) {
        Refresh-Path
        if (Test-Cmd $cmd) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Try-Do($label, [scriptblock]$action) {
    try {
        & $action
        Log 'OK' $label 'done'
        AddResult $label $true 'ok'
    }
    catch {
        Log 'ERR' $label $_.Exception.Message
        AddResult $label $false ($_.Exception.Message)
    }
}

# cache dirs
if ($CACHE.enabled) {
    $CACHE.npm_dir = if ($CACHE.npm_dir) { $CACHE.npm_dir } else { Join-Path $CACHE.root 'npm' }
    $CACHE.wheel_dir = if ($CACHE.wheel_dir) { $CACHE.wheel_dir } else { Join-Path $CACHE.root 'wheelhouse' }
    $CACHE.choco_dir = if ($CACHE.choco_dir) { $CACHE.choco_dir } else { Join-Path $CACHE.root 'choco' }
    New-Item -ItemType Directory -Force -Path $CACHE.root, $CACHE.npm_dir, $CACHE.wheel_dir, $CACHE.choco_dir | Out-Null
}

# --------------- bootstrap managers ----------------
function Ensure-Winget {
    if (-not (Test-Cmd winget)) {
        throw "winget not found. Install 'App Installer' from Microsoft Store, then rerun."
    }
}

function Ensure-Choco {
    if (-not (Test-Cmd choco)) {
        if ($CACHE.use_only) {
            Log 'ERR' 'choco' 'missing and cache-only mode enabled'
            AddResult 'choco' $false 'missing in cache-only mode'
            return
        }
        Log 'SKIP' 'choco' 'Bootstrapping Chocolatey...'
        Set-ExecutionPolicy Bypass -Scope Process -Force
        Try-Do 'choco' {
            iex "& { $(irm https://community.chocolatey.org/install.ps1) }"
        }
        Refresh-Path
        if (-not (Wait-ForCommand 'choco' 30)) {
            Log 'ERR' 'choco' 'Chocolatey not available after install'
        }
    }
    else {
        Log 'OK' 'choco' 'present'
    }
}

# --------------- version helpers ----------------
function Get-WingetVersion($id) {
    try {
        (winget list --id $id --exact 2>$null | Select-String -SimpleMatch $id | ForEach-Object { ($_ -split '\s{2,}')[-2] }) -join ''
    }
    catch { '' }
}

function Get-ChocoVersion($name) {
    try {
        (choco list --local-only --exact $name 2>$null) -replace '^.*\s([0-9][\w\.\-]+).*$', '$1'
    }
    catch { '' }
}

function Get-CmdVersion($cmd, $args = @('--version')) {
    try {
        if (-not (Test-Cmd $cmd)) {
            return ''
        }
        $out = & $cmd @args 2>$null
        if ($out) {
            return ($out | Select-Object -First 1).ToString().Trim()
        }
        return ''
    }
    catch { '' }
}

# --------------- installers ----------------
function Test-WingetInstalled($id) {
    $out = winget list --id $id --exact 2>$null
    return ($LASTEXITCODE -eq 0 -and ($out | Select-String -SimpleMatch $id))
}

function Install-Winget($id, $label) {
    if ($CACHE.use_only) {
        if ($WINGET_TO_CHOCO.ContainsKey($id)) {
            $alt = $WINGET_TO_CHOCO[$id]
            Install-Choco $alt "$label (choco fallback)"
            return
        }
        Log 'ERR' $label 'winget offline not supported in cache-only mode (no fallback mapping)'
        AddResult $label $false 'cache-only mode; no fallback' 'winget'
        return
    }
    if (Test-WingetInstalled $id) {
        Log 'SKIP' $label 'already installed'
        AddResult $label $true 'already installed' 'winget' (Get-WingetVersion $id)
        return
    }
    $ver = $VERS.winget[$id]
    Try-Do $label {
        $args = @('install', '--id', $id, '-e', '--accept-package-agreements', '--accept-source-agreements')
        if ($PINNED -and $ver) {
            $args += @('--version', $ver)
        }
        winget @args | Out-Null
    }
    AddResult $label $true 'ok' 'winget' (Get-WingetVersion $id)
}

function Test-ChocoInstalled($name) {
    $out = choco list --local-only --exact $name 2>$null
    return ($out -match "^$name ")
}

function Install-Choco($name, $label) {
    if (Test-ChocoInstalled $name) {
        AddResult $label $true 'already installed' 'choco' (Get-ChocoVersion $name)
        Log 'SKIP' $label 'already installed'
        return
    }
    $ver = $VERS.choco[$name]
    if ($CACHE.enabled -and $CACHE.prefetch -and -not $CACHE.use_only) {
        Try-Do "$label (prefetch)" {
            if ($PINNED -and $ver) {
                choco download $name --version=$ver --output-directory $CACHE.choco_dir | Out-Null
            }
            else {
                choco download $name --output-directory $CACHE.choco_dir | Out-Null
            }
        }
    }
    if ($CACHE.enabled -and $CACHE.use_only) {
        Try-Do $label {
            choco install $name -y --no-progress --source $CACHE.choco_dir | Out-Null
        }
    }
    else {
        Try-Do $label {
            if ($PINNED -and $ver) {
                choco install $name -y --no-progress --version=$ver | Out-Null
            }
            else {
                choco install $name -y --no-progress | Out-Null
            }
        }
    }
    AddResult $label $true 'ok' 'choco' (Get-ChocoVersion $name)
}

function Install-Npm($pkg, $cmd, $label) {
    if (Test-Cmd $cmd) {
        AddResult $label $true "command '$cmd' present" 'npm' (Get-CmdVersion $cmd)
        Log 'SKIP' $label "command '$cmd' present"
        return
    }
    if (-not (Wait-ForCommand 'npm' 10)) {
        Log 'ERR' $label 'npm not available'
        AddResult $label $false 'npm missing' 'npm'
        return
    }
    $ver = $VERS.npm[$pkg]
    $specifier = if ($PINNED -and $ver) { "$pkg@$ver" } else { $pkg }

    if ($CACHE.enabled -and $CACHE.prefetch -and -not $CACHE.use_only) {
        Try-Do "$label (prefetch)" {
            npm pack $specifier --pack-destination $CACHE.npm_dir | Out-Null
        }
    }
    if ($CACHE.enabled -and $CACHE.use_only) {
        $verSuffix = if ($PINNED -and $ver) { "-$ver" } else { "" }
        $tgz = Join-Path $CACHE.npm_dir ($pkg.Split('/')[-1] + $verSuffix + ".tgz")
        if (Test-Path $tgz) {
            Try-Do $label {
                npm install -g $tgz | Out-Null
            }
        }
        else {
            Log 'ERR' $label "missing cache artifact: $tgz"
            AddResult $label $false 'not in cache' 'npm'
        }
    }
    else {
        Try-Do $label {
            npm install -g $specifier | Out-Null
        }
    }
    AddResult $label $true 'ok' 'npm' (Get-CmdVersion $cmd)
}

function Find-Python {
    foreach ($c in @('py', 'python3', 'python')) {
        if (Test-Cmd $c) {
            return $c
        }
    }
    return $null
}

function Ensure-Pipx {
    if (-not (Test-Cmd pipx)) {
        if ($CACHE.use_only) {
            throw "pipx missing and cache-only mode is ON. Install Python/pipx first or disable cache-only."
        }
        Log 'SKIP' 'pipx' 'Bootstrapping pipx with Python...'
        Refresh-Path
        $py = Find-Python
        if (-not $py) {
            throw "Python not found after installation. Open a new terminal or rerun after Python is set."
        }
        Try-Do 'pipx-bootstrap' {
            & $py -m pip install --user --upgrade pip pipx | Out-Null
        }
        Try-Do 'pipx-ensurepath' {
            & $py -m pipx ensurepath | Out-Null
        }
        Refresh-Path
        $userBin = [IO.Path]::Combine($env:USERPROFILE, '.local', 'bin')
        if (-not ($env:PATH -split ';' -contains $userBin)) {
            $env:PATH += ";$userBin"
        }
        if (-not (Wait-ForCommand 'pipx' 30)) {
            throw "pipx not available in PATH after install; open a new terminal and rerun."
        }
    }
    else {
        Log 'OK' 'pipx' 'present'
    }
}

function Install-Pipx($pkg, $cmd, $label) {
    if ($cmd -and (Test-Cmd $cmd)) {
        AddResult $label $true "command '$cmd' present" 'pipx' (Get-CmdVersion $cmd)
        Log 'SKIP' $label "command '$cmd' present"
        return
    }
    $ver = $VERS.pipx[$pkg]
    $spec = if ($PINNED -and $ver) { "$pkg==$ver" } else { $pkg }
    if ($CACHE.enabled -and $CACHE.prefetch -and -not $CACHE.use_only) {
        Try-Do "$label (prefetch)" {
            $py = Find-Python
            if (-not $py) {
                throw "Python not detected for prefetch"
            }
            & $py -m pip download $spec -d $CACHE.wheel_dir | Out-Null
        }
    }
    if ($CACHE.enabled -and $CACHE.use_only) {
        Try-Do $label {
            pipx install $spec --pip-args="--no-index --find-links $($CACHE.wheel_dir)" | Out-Null
        }
    }
    else {
        Try-Do $label {
            pipx install $spec | Out-Null
        }
    }
    if ($cmd) {
        AddResult $label $true 'ok' 'pipx' (Get-CmdVersion $cmd)
    }
    else {
        AddResult $label $true 'ok' 'pipx' ''
    }
}

# --------------- RUN ---------------
Write-Host "`n=== STARTING CLI STACK INSTALLATION (VERIFIED PACKAGES ONLY) ===`n" -ForegroundColor Cyan

Ensure-Admin
Ensure-Winget
Ensure-Choco

# Core (winget)
Install-Winget 'Git.Git' 'Git'
Refresh-Path
Wait-ForCommand 'git' | Out-Null

Install-Winget 'Git.GitLFS' 'Git LFS'
Refresh-Path
Wait-ForCommand 'git' | Out-Null

Install-Winget 'GitHub.cli' 'GitHub CLI (gh)'
Install-Winget 'OpenJS.NodeJS.LTS' 'Node.js LTS'
Refresh-Path
Wait-ForCommand 'node' | Out-Null
Wait-ForCommand 'npm' | Out-Null

Install-Winget 'Python.Python.3.12' 'Python 3.12'
Refresh-Path
Wait-ForCommand 'py' | Out-Null

Install-Winget 'Microsoft.PowerShell' 'PowerShell 7'
Install-Winget 'Microsoft.VisualStudioCode' 'Visual Studio Code'
Install-Winget '7zip.7zip' '7-Zip'
Install-Winget 'jqlang.jq' 'jq'
Install-Winget 'MikeFarah.yq' 'yq'
Install-Winget 'BurntSushi.ripgrep.MSVC' 'ripgrep (rg)'
Install-Winget 'sharkdp.fd' 'fd'
Install-Winget 'Task.Task' 'Go Task'
Install-Winget 'AquaSecurity.Trivy' 'Trivy'
Install-Winget 'Ollama.Ollama' 'Ollama'
Install-Winget 'PostgreSQL.PostgreSQL' 'PostgreSQL (server)'
Install-Winget 'tporadowski.redis' 'Redis (Windows port)'

# GNU Make (Chocolatey)
Install-Choco 'make' 'GNU Make'

# Node package manager: pnpm via Corepack; fallback to npm
if (Test-Cmd node) {
    $pnpmOk = $false
    try {
        if (Wait-ForCommand 'corepack' 10) {
            Try-Do 'pnpm(Corepack enable)' {
                corepack enable | Out-Null
            }
            try {
                corepack prepare pnpm@((if ($PINNED -and $VERS.npm['pnpm']) { $VERS.npm['pnpm'] } else { 'latest' })) --activate | Out-Null
                $pnpmOk = (Test-Cmd pnpm)
            }
            catch {}
        }
    }
    catch {}
    if (-not $pnpmOk) {
        Install-Npm 'pnpm' 'pnpm' 'pnpm (npm fallback)'
    }
}
else {
    Log 'ERR' 'pnpm' 'Node.js not detected; pnpm skipped'
    AddResult 'pnpm' $false 'Node.js missing' 'npm'
}

# NPM global CLIs
Install-Npm '@anthropic-ai/claude-code' 'claude' 'Claude Code CLI'
Install-Npm '@google/gemini-cli' 'gemini' 'Gemini CLI'
Install-Npm 'openai' 'openai' 'OpenAI CLI'
Install-Npm '@github/copilot' 'github-copilot-cli' 'GitHub Copilot CLI'
Install-Npm 'prettier' 'prettier' 'Prettier'
Install-Npm 'eslint' 'eslint' 'ESLint'
Install-Npm 'pyright' 'pyright' 'pyright'
Install-Npm 'markdownlint-cli' 'markdownlint' 'markdownlint-cli'

# pipx bootstrap and tools
Ensure-Pipx

# linters / test / tooling (verified successful installations only)
Install-Pipx 'ruff' 'ruff' 'Ruff'
Install-Pipx 'black' 'black' 'Black'
Install-Pipx 'isort' 'isort' 'isort'
Install-Pipx 'pylint' 'pylint' 'Pylint'
Install-Pipx 'mypy' 'mypy' 'mypy'
Install-Pipx 'bandit' 'bandit' 'Bandit'
Install-Pipx 'safety' 'safety' 'Safety'
Install-Pipx 'semgrep' 'semgrep' 'Semgrep'
Install-Pipx 'yamllint' 'yamllint' 'yamllint'
Install-Pipx 'mdformat' 'mdformat' 'mdformat'
Install-Pipx 'codespell' 'codespell' 'codespell'
Install-Pipx 'pytest' 'pytest' 'pytest'

# Git LFS init
if (Test-Cmd git) {
    Try-Do 'git lfs install' {
        git lfs install | Out-Null
    }
}
else {
    Log 'SKIP' 'git lfs install' 'git not available; skipped'
    AddResult 'git lfs install' $false 'git missing' 'git'
}

# Not-installables (informational)
Log 'SKIP' 'unittest' 'Python stdlib — no install needed'
AddResult 'unittest (stdlib)' $true 'already available' 'stdlib' '3.x'
Log 'SKIP' 'Python GUI Terminal' 'custom app — skipped (not a package)'
AddResult 'Python GUI Terminal' $true 'not applicable' 'custom' ''

# --------------- REPORT (JSON/CSV) ---------------
function Normalize-Version($s) {
    if (-not $s) { return '' }
    ($s -split '[\s,]')[0]
}

# Try to enrich missing versions for common commands
$guessMap = @{
    'Git'                    = 'git'
    'Git LFS'                = 'git'
    'GitHub CLI (gh)'        = 'gh'
    'Node.js LTS'            = 'node'
    'Python 3.12'            = 'py'
    'PowerShell 7'           = 'pwsh'
    'Visual Studio Code'     = 'code'
    '7-Zip'                  = '7z'
    'jq'                     = 'jq'
    'yq'                     = 'yq'
    'ripgrep (rg)'           = 'rg'
    'fd'                     = 'fd'
    'Go Task'                = 'task'
    'Trivy'                  = 'trivy'
    'Ollama'                 = 'ollama'
    'Ruff'                   = 'ruff'
    'Black'                  = 'black'
    'isort'                  = 'isort'
    'Pylint'                 = 'pylint'
    'mypy'                   = 'mypy'
    'Bandit'                 = 'bandit'
    'Safety'                 = 'safety'
    'Semgrep'                = 'semgrep'
    'yamllint'               = 'yamllint'
    'mdformat'               = 'mdformat'
    'codespell'              = 'codespell'
    'pytest'                 = 'pytest'
    'Claude Code CLI'        = 'claude'
    'Gemini CLI'             = 'gemini'
    'OpenAI CLI'             = 'openai'
    'markdownlint-cli'       = 'markdownlint'
    'pyright'                = 'pyright'
    'pnpm (npm fallback)'    = 'pnpm'
}

$results = $results | ForEach-Object {
    if (-not $_.version -and $_.ok -and $guessMap.ContainsKey($_.name)) {
        $cmd = $guessMap[$_.name]
        $ver = switch ($cmd) {
            'node' { Get-CmdVersion 'node' @('--version') }
            'py' { Get-CmdVersion 'py' @('-V') }
            'code' { Get-CmdVersion 'code' @('--version') }
            default { Get-CmdVersion $cmd @('--version') }
        }
        $_.version = Normalize-Version $ver
    }
    $_
}

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$jsonPath = Join-Path $PWD "install_summary_$ts.json"
$csvPath = Join-Path $PWD "install_summary_$ts.csv"

$results | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $jsonPath
$results | Export-Csv -NoTypeInformation $csvPath

Write-Host "`n====================== INSTALL SUMMARY ======================" -ForegroundColor Cyan
$results | Sort-Object name | ForEach-Object {
    $color = if ($_.ok) { 'Green' } else { 'Red' }
    Write-Host ("{0,-30} : {1} {2}" -f $_.name, ($(if ($_.ok) { 'OK' } else { 'FAILED' })), (if ($_.version) { "[v$($_.version)]" } else { "" })) -ForegroundColor $color
    if (-not $_.ok) {
        Write-Host ("  ↳ details: {0}" -f $_.details) -ForegroundColor DarkYellow
    }
}

Write-Host "`nSaved report:" -ForegroundColor Cyan
Write-Host "  JSON: $jsonPath"
Write-Host "  CSV : $csvPath"
Write-Host "=============================================================`n" -ForegroundColor Cyan
Write-Host "`nPackages EXCLUDED from this script (not successfully installed):" -ForegroundColor Yellow
Write-Host "  - Nox (pipx)" -ForegroundColor DarkYellow
Write-Host "  - Aider (pipx)" -ForegroundColor DarkYellow
Write-Host "  - LangGraph CLI (pipx)" -ForegroundColor DarkYellow
Write-Host "  - Uvicorn (pipx)" -ForegroundColor DarkYellow
Write-Host "  - FastAPI (pipx inject)" -ForegroundColor DarkYellow
Write-Host "`nTo install missing packages manually:" -ForegroundColor Cyan
Write-Host "  pipx install nox" -ForegroundColor Gray
Write-Host "  pipx install aider-chat" -ForegroundColor Gray
Write-Host "  pipx install langgraph-cli" -ForegroundColor Gray
Write-Host "  pipx install uvicorn" -ForegroundColor Gray
Write-Host "  pipx inject uvicorn fastapi" -ForegroundColor Gray
Write-Host "`nTip: On a truly fresh machine, re-run once to catch tools that needed Node/Python on the first pass." -ForegroundColor DarkCyan
