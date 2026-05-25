param(
    [string]$Python = $env:STEFAN_PYTHON,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($Python)) {
    $DefaultPython = "D:\Anaconda\envs\py39\python.exe"
    if (Test-Path -LiteralPath $DefaultPython) {
        $Python = $DefaultPython
    } else {
        $Python = "python"
    }
}

Push-Location $ProjectRoot
try {
    & $Python -c "import platform, sys; assert platform.architecture()[0] == '64bit'; import PyQt6, PyInstaller; print(sys.version.split()[0], platform.architecture()[0])"

    if (-not $SkipTests) {
        & $Python -m unittest discover -s tests
    }

    $Resources = Join-Path $ProjectRoot "resources"
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name StefanSimulator `
        --paths src `
        --add-data "$Resources;resources" `
        --distpath dist `
        --workpath build `
        --specpath build `
        src\stefan_app\main.py

    $Executable = Join-Path $ProjectRoot "dist\StefanSimulator\StefanSimulator.exe"
    if (-not (Test-Path -LiteralPath $Executable)) {
        throw "Release executable was not found: $Executable"
    }

    Write-Host "Windows x64 release directory: $(Split-Path -Parent $Executable)"
    Write-Host "Executable: $Executable"
}
finally {
    Pop-Location
}
