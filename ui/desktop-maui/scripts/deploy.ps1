[CmdletBinding()]
param(
    [string]$Configuration,
    [string]$Framework,
    [string]$RuntimeIdentifier,
    [string]$PythonVersion,
    [switch]$SkipApiBuild,
    [switch]$SkipMauiPublish
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "deploy_config.ps1")

$config = Get-DeployConfig

if ([string]::IsNullOrWhiteSpace($Configuration)) {
    $Configuration = $config.Configuration
}

if ([string]::IsNullOrWhiteSpace($Framework)) {
    $Framework = $config.Framework
}

if ([string]::IsNullOrWhiteSpace($RuntimeIdentifier)) {
    $RuntimeIdentifier = $config.RuntimeIdentifier
}

if ([string]::IsNullOrWhiteSpace($PythonVersion)) {
    $PythonVersion = $config.PythonVersion
}

$publishRoot = $config.PublishRoot
$coreRoot = Join-Path $publishRoot "core"
$apiPublishRoot = Join-Path $coreRoot "api"
$pythonPublishRoot = Join-Path $coreRoot "python"
$uzoncalcPublishRoot = Join-Path $coreRoot "uzoncalc"
$mauiPublishRoot = Join-Path $publishRoot "maui"
$apiProjectRoot = $config.ApiRoot
$apiPortableOutputName = "desktop-maui-api-portable"
$apiPortableOutputRoot = Join-Path (Join-Path $apiProjectRoot "dist") $apiPortableOutputName
$apiBuildScript = Join-Path $apiProjectRoot "scripts\build-portable.ps1"
$mauiProjectFile = Join-Path $config.DesktopMauiRoot "uzoncalc\uzoncalc.csproj"
$uzoncalcSourceRoot = Join-Path $config.RepoRoot "uzoncalc"

function Write-Section {
    param([string]$Message)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info {
    param([string]$Message)

    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Remove-DirectoryIfExists {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Copy-DirectoryContents {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$ExcludeDirectoryNames = @(),
        [string[]]$ExcludeDirectoryPatterns = @(),
        [string[]]$ExcludeFilePatterns = @()
    )

    Ensure-Directory -Path $Destination

    $normalizedSource = [System.IO.Path]::GetFullPath($Source)
    $directories = Get-ChildItem -LiteralPath $normalizedSource -Directory -Recurse -Force

    foreach ($directory in $directories) {
        $directoryNameExcluded = ($ExcludeDirectoryNames -contains $directory.Name)
        if (-not $directoryNameExcluded) {
            foreach ($pattern in $ExcludeDirectoryPatterns) {
                if ($directory.Name -like $pattern) {
                    $directoryNameExcluded = $true
                    break
                }
            }
        }

        if ($directoryNameExcluded) {
            continue
        }

        $segments = $directory.FullName.Substring($normalizedSource.Length).TrimStart('\').Split('\', [System.StringSplitOptions]::RemoveEmptyEntries)
        $hasExcludedSegment = $false
        foreach ($segment in $segments) {
            if ($ExcludeDirectoryNames -contains $segment) {
                $hasExcludedSegment = $true
                break
            }

            foreach ($pattern in $ExcludeDirectoryPatterns) {
                if ($segment -like $pattern) {
                    $hasExcludedSegment = $true
                    break
                }
            }

            if ($hasExcludedSegment) {
                break
            }
        }

        if ($segments.Count -gt 0 -and $hasExcludedSegment) {
            continue
        }

        $targetDirectory = Join-Path $Destination $directory.FullName.Substring($normalizedSource.Length).TrimStart('\')
        Ensure-Directory -Path $targetDirectory
    }

    $files = Get-ChildItem -LiteralPath $normalizedSource -File -Recurse -Force
    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($normalizedSource.Length).TrimStart('\')
        $segments = $relativePath.Split('\', [System.StringSplitOptions]::RemoveEmptyEntries)
        $hasExcludedParent = $false
        if ($segments.Count -gt 1) {
            foreach ($segment in $segments[0..($segments.Count - 2)]) {
                if ($ExcludeDirectoryNames -contains $segment) {
                    $hasExcludedParent = $true
                    break
                }

                foreach ($pattern in $ExcludeDirectoryPatterns) {
                    if ($segment -like $pattern) {
                        $hasExcludedParent = $true
                        break
                    }
                }

                if ($hasExcludedParent) {
                    break
                }
            }
        }

        if ($hasExcludedParent) {
            continue
        }

        $isExcluded = $false
        foreach ($pattern in $ExcludeFilePatterns) {
            if ($file.Name -like $pattern) {
                $isExcluded = $true
                break
            }
        }

        if ($isExcluded) {
            continue
        }

        $destinationFile = Join-Path $Destination $relativePath
        $destinationDirectory = Split-Path -Parent $destinationFile
        Ensure-Directory -Path $destinationDirectory
        Copy-Item -LiteralPath $file.FullName -Destination $destinationFile -Force
    }
}

function Remove-MatchingPaths {
    param(
        [string]$Root,
        [string[]]$DirectoryNames = @(),
        [string[]]$DirectoryPatterns = @(),
        [string[]]$FilePatterns = @()
    )

    if (-not (Test-Path -LiteralPath $Root)) {
        return
    }

    $directories = Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force |
        Sort-Object FullName -Descending

    foreach ($directory in $directories) {
        $shouldRemove = ($DirectoryNames -contains $directory.Name)
        if (-not $shouldRemove) {
            foreach ($pattern in $DirectoryPatterns) {
                if ($directory.Name -like $pattern) {
                    $shouldRemove = $true
                    break
                }
            }
        }

        if ($shouldRemove) {
            Remove-Item -LiteralPath $directory.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    $files = Get-ChildItem -LiteralPath $Root -File -Recurse -Force
    foreach ($file in $files) {
        foreach ($pattern in $FilePatterns) {
            if ($file.Name -like $pattern) {
                Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue
                break
            }
        }
    }
}

Write-Section "Prepare output directories"

Write-Info "Cleaning existing directory: $publishRoot"
Remove-DirectoryIfExists -Path $publishRoot

foreach ($path in @($publishRoot, $coreRoot, $apiPublishRoot, $pythonPublishRoot, $uzoncalcPublishRoot, $mauiPublishRoot)) {
    Ensure-Directory -Path $path
}

if (-not $SkipApiBuild) {
    Write-Section "Build portable API bundle"

    if (-not (Test-Path -LiteralPath $apiBuildScript)) {
        throw "API build script was not found: $apiBuildScript"
    }

    & $apiBuildScript -OutputName $apiPortableOutputName -PythonVersion $PythonVersion

    if (-not (Test-Path -LiteralPath $apiPortableOutputRoot)) {
        throw "Portable API output was not found: $apiPortableOutputRoot"
    }

    Write-Info "Copying API files into: $apiPublishRoot"
    foreach ($item in @("app", "config", "data", "utils", "main.py", "requirements.txt")) {
        $sourcePath = Join-Path $apiPortableOutputRoot $item
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            throw "Portable API output is missing required content: $sourcePath"
        }

        Copy-Item -LiteralPath $sourcePath -Destination $apiPublishRoot -Recurse -Force
    }

    $pythonSourceRoot = Join-Path $apiPortableOutputRoot "dist\python-embedded"
    if (-not (Test-Path -LiteralPath $pythonSourceRoot)) {
        throw "Portable API output is missing embedded Python: $pythonSourceRoot"
    }

    Write-Info "Copying embedded Python into: $pythonPublishRoot"
    Copy-Item -Path (Join-Path $pythonSourceRoot "*") -Destination $pythonPublishRoot -Recurse -Force
} else {
    Write-Section "Skip API build"
    Write-Info "Created empty directory: $apiPublishRoot"
    Write-Info "Created empty directory: $pythonPublishRoot"
}

Write-Section "Copy uzoncalc"

if (-not (Test-Path -LiteralPath $uzoncalcSourceRoot)) {
    throw "uzoncalc source directory was not found: $uzoncalcSourceRoot"
}

Copy-DirectoryContents `
    -Source $uzoncalcSourceRoot `
    -Destination $uzoncalcPublishRoot `
    -ExcludeDirectoryNames @("__pycache__", ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache", "dist", "build", ".tox", ".nox", ".vscode") `
    -ExcludeDirectoryPatterns @("*.egg-info") `
    -ExcludeFilePatterns @("*.pyc", "*.pyo", "*.egg-info")

Remove-MatchingPaths `
    -Root $uzoncalcPublishRoot `
    -DirectoryNames @("__pycache__", ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache", "dist", "build", ".tox", ".nox", ".vscode") `
    -DirectoryPatterns @("*.egg-info") `
    -FilePatterns @("*.pyc", "*.pyo")

if (-not $SkipMauiPublish) {
    Write-Section "Publish MAUI Windows app"

    if (-not (Test-Path -LiteralPath $mauiProjectFile)) {
        throw "MAUI project file was not found: $mauiProjectFile"
    }

    $publishArgs = @(
        "publish"
        $mauiProjectFile
        "-c"
        $Configuration
        "-f"
        $Framework
        "--self-contained"
        "false"
        "-p:WindowsPackageType=None"
        "-p:AppxPackage=false"
        "-o"
        $mauiPublishRoot
    )

    if (-not [string]::IsNullOrWhiteSpace($RuntimeIdentifier)) {
        Write-Info "Publishing MAUI app with runtime identifier: $RuntimeIdentifier"
        $publishArgs += @("-r", $RuntimeIdentifier)
    } else {
        Write-Info "Publishing MAUI app without an explicit runtime identifier"
    }

    & dotnet @publishArgs
} else {
    Write-Section "Skip MAUI publish"
    Write-Info "Created empty directory: $mauiPublishRoot"
}

Write-Section "Done"

Write-Info "publish/win root: $publishRoot"
Write-Info "API directory: $apiPublishRoot"
Write-Info "Python directory: $pythonPublishRoot"
Write-Info "uzoncalc directory: $uzoncalcPublishRoot"
Write-Info "MAUI directory: $mauiPublishRoot"
Write-Host ""
Write-Host "Suggested verification commands:" -ForegroundColor Cyan
Write-Host "  powershell -ExecutionPolicy Bypass -File ui\desktop-maui\scripts\deploy.ps1"
Write-Host ('  Test-Path "{0}"' -f (Join-Path $pythonPublishRoot "python.exe"))
Write-Host ('  Test-Path "{0}"' -f (Join-Path $apiPublishRoot "main.py"))
Write-Host ('  Get-ChildItem "{0}"' -f $mauiPublishRoot)
