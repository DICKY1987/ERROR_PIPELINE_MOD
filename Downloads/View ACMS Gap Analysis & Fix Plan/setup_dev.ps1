<#
.SYNOPSIS
    ACMS Development Environment Setup Script for Windows
.DESCRIPTION
    Sets up Python virtual environment and installs ACMS package with dev dependencies
.VERSION
    1.0.0
.DATE
    2025-11-02
.OWNER
    Platform.Engineering
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up ACMS development environment..." -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "📋 Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1 | Select-String -Pattern "\d+\.\d+\.\d+" | ForEach-Object { $_.Matches.Value }
    $requiredVersion = [Version]"3.11.0"
    $currentVersion = [Version]$pythonVersion
    
    if ($currentVersion -lt $requiredVersion) {
        Write-Host "❌ Python $requiredVersion or higher is required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Python $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11 or higher." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Virtual environment already exists" -ForegroundColor Cyan
}
Write-Host ""

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✅ pip upgraded" -ForegroundColor Green
Write-Host ""

# Install package in editable mode with dev dependencies
Write-Host "📚 Installing ACMS package in editable mode with dev dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]" --quiet
Write-Host "✅ Package installed successfully" -ForegroundColor Green
Write-Host ""

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env file created from .env.example" -ForegroundColor Green
        Write-Host "⚠️  Please update .env with your configuration" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  No .env.example found - skipping .env creation" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Run tests to verify setup
Write-Host "🧪 Running tests to verify setup..." -ForegroundColor Yellow
try {
    pytest -v --tb=short -x
    Write-Host ""
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "⚠️  Some tests failed - please review the output above" -ForegroundColor Yellow
}
Write-Host ""

# Print next steps
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Activate the virtual environment: .\.venv\Scripts\Activate.ps1"
Write-Host "  2. Update .env with your configuration"
Write-Host "  3. Run tests: pytest -v"
Write-Host "  4. Run linting: black . ; ruff check ."
Write-Host "  5. Check types: mypy core/"
Write-Host ""
Write-Host "📖 For more information, see README.md" -ForegroundColor Cyan
Write-Host ""
