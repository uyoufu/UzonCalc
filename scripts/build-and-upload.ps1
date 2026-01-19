<#
.SYNOPSIS
    Build the project and upload distributions to PyPI or TestPyPI.

.DESCRIPTION
    Installs build/twine (unless skipped), runs `python -m build` to produce
    sdist and wheel, removes any .egg files, then uploads allowed distributions.

.PARAMETER UseTestPyPI
    If present, upload to TestPyPI instead of the default PyPI endpoint.

.PARAMETER SkipInstall
    If present, skip installing/upgrading `build` and `twine`.

.EXAMPLE
    .\build-and-upload.ps1

.EXAMPLE
    .\build-and-upload.ps1 -UseTestPyPI
#>

[CmdletBinding()]
param(
  [switch]$UseTestPyPI,
  [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-ErrAndExit($msg, $code = 1) {
  Write-Host $msg -ForegroundColor Red
  exit $code
}

Write-Host "Starting build and upload script..."
# Determine project root as the parent of the script folder so this script
# can be executed from anywhere and still operate on the repository root.
$scriptDir = Split-Path -Path $PSCommandPath -Parent
$projectRoot = Split-Path -Path $scriptDir -Parent

Write-Host "Project root: $projectRoot"

# Ensure python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-ErrAndExit "Python is not found in PATH. Please install Python and retry."
}

Push-Location $projectRoot
try {
  if (-not $SkipInstall) {
    Write-Host "Ensuring pip, build and twine are installed/updated..."
    python -m pip install --upgrade pip > $null
    python -m pip install --upgrade build twine
  }

  if (-not (Test-Path -Path "dist")) {
    New-Item -Path "dist" -ItemType Directory | Out-Null
  }

  Write-Host "Removing old .egg files from dist/ (if any)..."
  Get-ChildItem -Path dist -Filter *.egg -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

  Write-Host "Running build (sdist + wheel) in $projectRoot..."
  python -m build
  if ($LASTEXITCODE -ne 0) { Write-ErrAndExit "Build failed (exit code $LASTEXITCODE)." $LASTEXITCODE }

  $sdist = Get-ChildItem -Path dist -Filter *.tar.gz -File -ErrorAction SilentlyContinue
  $wheels = Get-ChildItem -Path dist -Filter *.whl -File -ErrorAction SilentlyContinue

  if ((-not $sdist) -and (-not $wheels)) {
    Write-ErrAndExit "No sdist (.tar.gz) or wheel (.whl) found in dist/. Aborting."
  }

  if ($UseTestPyPI) {
    Write-Host "Uploading to TestPyPI (https://test.pypi.org/legacy/)..."
    python -m twine upload --repository-url https://test.pypi.org/legacy/ dist\*  
  }
  else {
    Write-Host "Uploading to PyPI (default repository, use --repository or .pypirc to change)..."
    python -m twine upload dist\*
  }

  if ($LASTEXITCODE -ne 0) {
    Write-ErrAndExit "twine upload failed (exit code $LASTEXITCODE)." $LASTEXITCODE
  }

  Write-Host "Upload complete."
}
finally {
  Pop-Location
}
