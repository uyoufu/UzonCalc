<#
.SYNOPSIS
    Build the project and upload distributions to PyPI or TestPyPI.

.DESCRIPTION
    Installs build/twine (unless skipped), runs `python -m build` to produce
    sdist and wheel, removes old distributions, then uploads the current build.

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

function Get-DistributionFiles {
  $patterns = @("*.egg", "*.tar.gz", "*.whl")
  $files = foreach ($pattern in $patterns) {
    Get-ChildItem -Path dist -Filter $pattern -File -ErrorAction SilentlyContinue
  }

  return @($files | Sort-Object -Property FullName -Unique)
}

Write-Host "Starting build and upload script..."
# Determine project root as the parent of the script folder so this script
# can be executed from anywhere and still operate on the repository root.
$scriptDir = Split-Path -Path $PSCommandPath -Parent
$projectRoot = Split-Path -Path $scriptDir -Parent
$buildRoot = Join-Path $projectRoot "uzoncalc"

Write-Host "Project root: $projectRoot"
Write-Host "Build root:   $buildRoot"

# Ensure python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-ErrAndExit "Python is not found in PATH. Please install Python and retry."
}

Push-Location $buildRoot
try {
  if (-not $SkipInstall) {
    Write-Host "Ensuring pip, build and twine are installed/updated..."
    python -m pip install --upgrade pip > $null
    python -m pip install --upgrade build twine
  }

  if (-not (Test-Path -Path "dist")) {
    New-Item -Path "dist" -ItemType Directory | Out-Null
  }

  $distFilesBeforeBuild = @{}
  foreach ($file in Get-DistributionFiles) {
    $distFilesBeforeBuild[$file.FullName] = $file.LastWriteTimeUtc
  }

  Write-Host "Running build (sdist + wheel) in $projectRoot..."
  python -m build
  if ($LASTEXITCODE -ne 0) { Write-ErrAndExit "Build failed (exit code $LASTEXITCODE)." $LASTEXITCODE }

  $distFilesAfterBuild = Get-DistributionFiles
  $builtDistributions = @(
    $distFilesAfterBuild | Where-Object {
      (-not $distFilesBeforeBuild.ContainsKey($_.FullName)) -or
      ($_.LastWriteTimeUtc -gt $distFilesBeforeBuild[$_.FullName])
    }
  )

  $builtUploadDistributions = @(
    $builtDistributions | Where-Object {
      ($_.Name -like "*.tar.gz") -or ($_.Name -like "*.whl")
    }
  )

  if (-not $builtUploadDistributions) {
    Write-ErrAndExit "No sdist (.tar.gz) or wheel (.whl) found in dist/. Aborting."
  }

  $builtDistributionFullNames = @($builtDistributions | ForEach-Object { $_.FullName })
  $oldDistributions = @(
    $distFilesAfterBuild | Where-Object { $builtDistributionFullNames -notcontains $_.FullName }
  )

  if ($oldDistributions) {
    Write-Host "Removing old distribution files from dist/..."
    $oldDistributions | ForEach-Object {
      Write-Host "  Removing $($_.Name)"
      Remove-Item -LiteralPath $_.FullName -Force
    }
  }

  $builtDistributionPaths = @($builtUploadDistributions | ForEach-Object { $_.FullName })

  if ($UseTestPyPI) {
    Write-Host "Uploading to TestPyPI (https://test.pypi.org/legacy/)..."
    python -m twine upload --repository-url https://test.pypi.org/legacy/ --verbose $builtDistributionPaths
  }
  else {
    Write-Host "Uploading to PyPI (default repository, use --repository or .pypirc to change)..."
    python -m twine upload --verbose $builtDistributionPaths
  }

  if ($LASTEXITCODE -ne 0) {
    Write-ErrAndExit "twine upload failed (exit code $LASTEXITCODE)." $LASTEXITCODE
  }

  Write-Host "Upload complete."
}
finally {
  Pop-Location
}
