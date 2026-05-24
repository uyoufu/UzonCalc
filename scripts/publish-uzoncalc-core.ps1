<#
.SYNOPSIS
    Build the project and upload distributions to PyPI or TestPyPI.

.DESCRIPTION
    Runs `python -m build` for src/core via uv to produce sdist and wheel, removes
    old distributions, then uploads the current build via twine.

.PARAMETER UseTestPyPI
    If present, upload to TestPyPI instead of the default PyPI endpoint.

.EXAMPLE
    .\build-and-upload.ps1

.EXAMPLE
    .\build-and-upload.ps1 -UseTestPyPI
#>

[CmdletBinding()]
param(
  [switch]$UseTestPyPI
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-ErrAndExit($msg, $code = 1) {
  # 输出错误信息并使用指定退出码终止脚本。
  Write-Host $msg -ForegroundColor Red
  exit $code
}

function Get-DistributionFiles {
  # 获取当前构建目录中的可发布文件，避免上传旧产物。
  $patterns = @("*.egg", "*.tar.gz", "*.whl")
  $files = foreach ($pattern in $patterns) {
    Get-ChildItem -Path (Join-Path $buildRoot "dist") -Filter $pattern -File -ErrorAction SilentlyContinue
  }

  return @($files | Sort-Object -Property FullName -Unique)
}

function Clear-BuildArtifacts {
  # 清理构建缓存，确保本次发布只使用当前源码生成的产物。
  $paths = @(
    (Join-Path $buildRoot "dist"),
    (Join-Path $buildRoot "build"),
    (Join-Path $buildRoot "uzoncalc.egg-info"),
    # 目录上移后，清理旧位置残留产物，避免误读历史构建结果。
    (Join-Path $buildRoot "uzoncalc\dist"),
    (Join-Path $buildRoot "uzoncalc\build"),
    (Join-Path $buildRoot "uzoncalc\uzoncalc.egg-info")
  )
  foreach ($path in $paths) {
    if (Test-Path -LiteralPath $path) {
      Write-Host "Removing stale build artifact: $path"
      Remove-Item -LiteralPath $path -Recurse -Force
    }
  }
}

function Test-ArchiveContains {
  # 使用 uv 提供的 Python 标准库检查归档内容，避免依赖当前 venv 的 pip。
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

  uv run --no-project python -c $pythonCode $ArchivePath @RequiredEntries
  if ($LASTEXITCODE -ne 0) {
    Write-ErrAndExit "Distribution content validation failed for $ArchivePath." $LASTEXITCODE
  }
}

function Test-DistributionFiles {
  # 校验 wheel 和 sdist 的关键入口文件，降低空包或漏资源上传风险。
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
# 核心包项目根目录为 src/core，包内名称仍保持 uzoncalc。
$buildRoot = Join-Path $projectRoot "src/core"

Write-Host "Project root: $projectRoot"
Write-Host "Build root:   $buildRoot"

# 确保发布流程可通过 uv 临时运行构建和上传工具。
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-ErrAndExit "uv is not found in PATH. Please install uv and retry."
}

Push-Location $buildRoot
try {
  # 每次发布前清理构建缓存，避免旧的空包或错误产物被上传。
  Clear-BuildArtifacts

  Write-Host "Running build (sdist + wheel) in $buildRoot..."
  uv run --no-project --with build python -m build
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
    uv run --no-project --with twine python -m twine upload --repository-url https://test.pypi.org/legacy/ --verbose $builtDistributionPaths
  }
  else {
    Write-Host "Uploading to PyPI (default repository, use --repository or .pypirc to change)..."
    uv run --no-project --with twine python -m twine upload --verbose $builtDistributionPaths
  }

  if ($LASTEXITCODE -ne 0) {
    Write-ErrAndExit "twine upload failed (exit code $LASTEXITCODE)." $LASTEXITCODE
  }

  Write-Host "Upload complete."
}
finally {
  Pop-Location
}
