<#
.SYNOPSIS
    Build the project and upload distributions to PyPI or TestPyPI.

.DESCRIPTION
    Installs build/twine (unless skipped), runs `python -m build` for uzoncalc/ to produce
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
    Get-ChildItem -Path (Join-Path $buildRoot "dist") -Filter $pattern -File -ErrorAction SilentlyContinue
  }

  return @($files | Sort-Object -Property FullName -Unique)
}

function Clear-BuildArtifacts {
  $paths = @(
    (Join-Path $buildRoot "dist"),
    (Join-Path $buildRoot "build"),
    (Join-Path $buildRoot "uzoncalc.egg-info")
  )
  foreach ($path in $paths) {
    if (Test-Path -LiteralPath $path) {
      Write-Host "Removing stale build artifact: $path"
      Remove-Item -LiteralPath $path -Recurse -Force
    }
  }
}

function Test-ArchiveContains {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ArchivePath,

    [Parameter(Mandatory = $true)]
    [string[]]$RequiredEntries
  )

  $pythonCode = @"
import sys
import tarfile
import zipfile
from pathlib import Path

archive_path = Path(sys.argv[1])
required_entries = sys.argv[2:]

if archive_path.suffix == ".whl":
    with zipfile.ZipFile(archive_path) as archive_file:
        names = set(archive_file.namelist())
    missing = [entry for entry in required_entries if entry not in names]
else:
    with tarfile.open(archive_path) as archive_file:
        names = set(archive_file.getnames())
    missing = [
        entry for entry in required_entries
        if not any(name.endswith(entry) for name in names)
    ]

if missing:
    print(f"{archive_path} missing required entries: {', '.join(missing)}")
    sys.exit(1)
"@

  python -c $pythonCode $ArchivePath @RequiredEntries
  if ($LASTEXITCODE -ne 0) {
    Write-ErrAndExit "Distribution content validation failed for $ArchivePath." $LASTEXITCODE
  }
}

function Test-DistributionFiles {
  param(
    [Parameter(Mandatory = $true)]
    [object[]]$DistributionFiles
  )

  $wheelFiles = @($DistributionFiles | Where-Object { $_.Name -like "*.whl" })
  $sdistFiles = @($DistributionFiles | Where-Object { $_.Name -like "*.tar.gz" })

  if (-not $wheelFiles) {
    Write-ErrAndExit "No wheel (.whl) found in built distributions. Aborting."
  }

  if (-not $sdistFiles) {
    Write-ErrAndExit "No sdist (.tar.gz) found in built distributions. Aborting."
  }

  $requiredWheelEntries = @(
    "uzoncalc/__init__.py",
    "uzoncalc/startup.py",
    "uzoncalc/template/calc_template.html"
  )
  $requiredSdistEntries = @(
    "pyproject.toml",
    "__init__.py",
    "template/calc_template.html"
  )

  foreach ($wheelFile in $wheelFiles) {
    Test-ArchiveContains -ArchivePath $wheelFile.FullName -RequiredEntries $requiredWheelEntries
  }

  foreach ($sdistFile in $sdistFiles) {
    Test-ArchiveContains -ArchivePath $sdistFile.FullName -RequiredEntries $requiredSdistEntries
  }
}

Write-Host "Starting build and upload script..."
# Determine project root as the parent of the script folder so this script
# can be executed from anywhere and still operate on the repository root.
$scriptDir = Split-Path -Path $PSCommandPath -Parent
$projectRoot = Split-Path -Path $scriptDir -Parent
# 核心包源码已迁移到 src/uzoncalc，包内名称仍保持 uzoncalc。
$buildRoot = Join-Path $projectRoot "src/uzoncalc"

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

  # 每次发布前清理构建缓存，避免旧的空包或错误产物被上传。
  Clear-BuildArtifacts

  Write-Host "Running build (sdist + wheel) in $buildRoot..."
  python -m build
  if ($LASTEXITCODE -ne 0) { Write-ErrAndExit "Build failed (exit code $LASTEXITCODE)." $LASTEXITCODE }

  $distFilesAfterBuild = Get-DistributionFiles
  $builtUploadDistributions = @(
    $distFilesAfterBuild | Where-Object {
      ($_.Name -like "*.tar.gz") -or ($_.Name -like "*.whl")
    }
  )

  if (-not $builtUploadDistributions) {
    Write-ErrAndExit "No sdist (.tar.gz) or wheel (.whl) found in dist/. Aborting."
  }

  Write-Host "Validating distribution contents before upload..."
  Test-DistributionFiles -DistributionFiles $builtUploadDistributions

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
