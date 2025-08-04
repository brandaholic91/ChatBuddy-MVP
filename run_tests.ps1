# ChatBuddy MVP Test Runner Script
# Egyszerűsített teszt futtatás kényelmi funkciókkal

param(
    [string]$TestFile = "",
    [string]$TestClass = "",
    [string]$TestFunction = "",
    [switch]$AllTests,
    [switch]$MarketingTests,
    [switch]$OrderStatusTests,
    [switch]$ProductInfoTests,
    [switch]$RecommendationsTests,
    [switch]$SecurityTests,
    [switch]$RateLimitingTests,
    [switch]$CoordinatorTests,
    [switch]$NoWarnings
)

# Alapértelmezett opciók - konzisztens teszt futtatás
$pytestArgs = @("-v", "--tb=short")

# Opcionális figyelmeztetés elnyomás (csak ha explicit módon kérték)
if ($NoWarnings) {
    $pytestArgs = @("-W", "ignore") + $pytestArgs
}

# Teszt kiválasztás
if ($AllTests) {
    $testPath = "tests/"
} elseif ($MarketingTests) {
    $testPath = "tests/test_marketing_agent.py"
} elseif ($OrderStatusTests) {
    $testPath = "tests/test_order_status_agent.py"
} elseif ($ProductInfoTests) {
    $testPath = "tests/test_product_info_agent.py"
} elseif ($RecommendationsTests) {
    $testPath = "tests/test_recommendations_agent.py"
} elseif ($SecurityTests) {
    $testPath = "tests/test_security.py"
} elseif ($RateLimitingTests) {
    $testPath = "tests/test_rate_limiting.py"
} elseif ($CoordinatorTests) {
    $testPath = "tests/test_coordinator.py"
} elseif ($TestFile -ne "") {
    $testPath = $TestFile
} else {
    $testPath = "tests/"
}

# Ha meg van adva teszt osztály vagy függvény
if ($TestClass -ne "") {
    $testPath += "::" + $TestClass
    if ($TestFunction -ne "") {
        $testPath += "::" + $TestFunction
    }
} elseif ($TestFunction -ne "") {
    $testPath += "::" + $TestFunction
}

# Teszt futtatása
Write-Host "Futtatás: python -m pytest $($pytestArgs -join ' ') $testPath" -ForegroundColor Green
& python -m pytest $pytestArgs $testPath

# Kilépési kód visszaadása
exit $LASTEXITCODE 