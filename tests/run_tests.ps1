# ChatBuddy MVP Test Runner Script
# PowerShell script for running comprehensive tests

param(
    [string]$TestType = "all",
    [string]$Markers = "",
    [switch]$Verbose,
    [switch]$Coverage,
    [switch]$Parallel,
    [switch]$Slow,
    [switch]$Unit,
    [switch]$Integration,
    [switch]$Security,
    [switch]$Performance,
    [switch]$Help
)

# Help function
function Show-Help {
    Write-Host @"
ChatBuddy MVP Test Runner

Usage: .\run_tests.ps1 [options]

Options:
    -TestType <type>     Test type: all, unit, integration, security, performance
    -Markers <markers>   Specific pytest markers to run
    -Verbose            Run with verbose output
    -Coverage           Generate coverage report
    -Parallel           Run tests in parallel
    -Slow               Include slow tests
    -Unit               Run only unit tests
    -Integration        Run only integration tests
    -Security           Run only security tests
    -Performance        Run only performance tests
    -Help               Show this help message

Examples:
    .\run_tests.ps1 -Unit -Coverage
    .\run_tests.ps1 -Integration -Verbose
    .\run_tests.ps1 -Markers "agent and not slow"
    .\run_tests.ps1 -TestType security -Parallel
"@
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Set Python path and environment
$env:PYTHONPATH = "."
$env:PYTHONUNBUFFERED = "1"

# Base pytest command
$pytestCmd = "python -m pytest"

# Add test path
$pytestCmd += " tests/"

# Configure based on parameters
if ($Verbose) {
    $pytestCmd += " -v -s"
}

if ($Coverage) {
    $pytestCmd += " --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80"
}

if ($Parallel) {
    $pytestCmd += " -n auto"
}

# Configure test type and markers
$markerArgs = @()

if ($Unit) {
    $markerArgs += "unit"
}

if ($Integration) {
    $markerArgs += "integration"
}

if ($Security) {
    $markerArgs += "security"
}

if ($Performance) {
    $markerArgs += "performance"
}

# Handle TestType parameter
switch ($TestType.ToLower()) {
    "unit" {
        $markerArgs += "unit"
    }
    "integration" {
        $markerArgs += "integration"
    }
    "security" {
        $markerArgs += "security"
    }
    "performance" {
        $markerArgs += "performance"
    }
    "agent" {
        $markerArgs += "agent"
    }
    "workflow" {
        $markerArgs += "workflow"
    }
    "database" {
        $markerArgs += "database"
    }
    "marketing" {
        $markerArgs += "marketing"
    }
    "api" {
        $markerArgs += "api"
    }
    "ai" {
        $markerArgs += "ai"
    }
    "all" {
        # Run all tests
    }
    default {
        Write-Host "Unknown test type: $TestType"
        Show-Help
        exit 1
    }
}

# Add custom markers if specified
if ($Markers) {
    $markerArgs += $Markers.Split(" ")
}

# Build marker string
if ($markerArgs.Count -gt 0) {
    $markerString = $markerArgs -join " and "
    $pytestCmd += " -m `"$markerString`""
}

# Exclude slow tests unless specifically requested
if (-not $Slow) {
    $pytestCmd += " -m `"not slow`""
}

# Add additional options
$pytestCmd += " --tb=short --strict-markers --disable-warnings"

# Display command
Write-Host "Running tests with command: $pytestCmd" -ForegroundColor Green
Write-Host ""

# Run tests
try {
    Invoke-Expression $pytestCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ All tests passed successfully!" -ForegroundColor Green
        
        if ($Coverage) {
            Write-Host ""
            Write-Host "📊 Coverage report generated in htmlcov/index.html" -ForegroundColor Cyan
        }
    } else {
        Write-Host ""
        Write-Host "❌ Some tests failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    exit 1
}

# Additional test utilities
function Run-QuickTests {
    Write-Host "Running quick tests..." -ForegroundColor Yellow
    python -m pytest tests/ -m "not slow and not integration" -v --tb=short
}

function Run-FullTestSuite {
    Write-Host "Running full test suite..." -ForegroundColor Yellow
    python -m pytest tests/ -v --tb=short --cov=src --cov-report=html --cov-report=term-missing
}

function Run-SecurityTests {
    Write-Host "Running security tests..." -ForegroundColor Yellow
    python -m pytest tests/ -m "security" -v --tb=short
}

function Run-PerformanceTests {
    Write-Host "Running performance tests..." -ForegroundColor Yellow
    python -m pytest tests/ -m "performance" -v --tb=short
}

function Show-TestSummary {
    Write-Host ""
    Write-Host "Test Summary:" -ForegroundColor Cyan
    Write-Host "  Unit tests: python -m pytest tests/ -m unit"
    Write-Host "  Integration tests: python -m pytest tests/ -m integration"
    Write-Host "  Security tests: python -m pytest tests/ -m security"
    Write-Host "  Performance tests: python -m pytest tests/ -m performance"
    Write-Host "  Agent tests: python -m pytest tests/ -m agent"
    Write-Host "  Workflow tests: python -m pytest tests/ -m workflow"
    Write-Host "  Database tests: python -m pytest tests/ -m database"
    Write-Host "  Marketing tests: python -m pytest tests/ -m marketing"
    Write-Host "  API tests: python -m pytest tests/ -m api"
    Write-Host "  AI tests: python -m pytest tests/ -m ai"
}

# Export functions for use in other scripts
Export-ModuleMember -Function Run-QuickTests, Run-FullTestSuite, Run-SecurityTests, Run-PerformanceTests, Show-TestSummary 