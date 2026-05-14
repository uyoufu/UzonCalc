<#
.SYNOPSIS
    Build the Windows desktop package.

.DESCRIPTION
    Builds the Tauri desktop executable and the API portable package, then
    combines both outputs into publish\win-x64.
#>

[CmdletBinding()]
param(
    [string]$OutputDir,
    [string]$ApiOutputName = "UzonCalc-Portable",
    [string]$PythonVersion = "3.11.9"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Join-RepoPath {
    param(
        [string]$Root,
        [string]$RelativePath
    )

    return [System.IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
}

function Resolve-OutputPath {
    param(
        [string]$Root,
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return (Join-RepoPath $Root "publish\win-x64")
    }

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return (Join-RepoPath $Root $Path)
}

function Assert-PathExists {
    param(
        [string]$Path,
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Description 不存在: $Path"
    }
}

function Assert-IsInsidePath {
    param(
        [string]$Path,
        [string]$ParentPath
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    $fullParentPath = [System.IO.Path]::GetFullPath($ParentPath).TrimEnd('\', '/')

    if (-not $fullPath.StartsWith($fullParentPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "输出目录必须位于项目目录内: $fullPath"
    }
}

function Invoke-ExternalCommand {
    param(
        [string]$FailureMessage,
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage，退出码: $LASTEXITCODE"
    }
}

function Copy-DirectoryContents {
    param(
        [string]$Source,
        [string]$Destination
    )

    Assert-PathExists $Source "源目录"

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }

    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
    }
}

function Get-LatestReleaseExe {
    param(
        [string]$ReleaseDirectory,
        [datetime]$BuildStartedAt
    )

    Assert-PathExists $ReleaseDirectory "Tauri release 目录"

    $exe = Get-ChildItem -LiteralPath $ReleaseDirectory -Filter "*.exe" -File |
        Where-Object { $_.LastWriteTime -ge $BuildStartedAt.AddSeconds(-5) } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $exe) {
        throw "未找到本次 Tauri 构建生成的 exe: $ReleaseDirectory"
    }

    return $exe.FullName
}

$scriptDir = Split-Path -Path $PSCommandPath -Parent
$repoRoot = Split-Path -Path $scriptDir -Parent
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)

$webDir = Join-RepoPath $repoRoot "ui\web"
$tauriDir = Join-RepoPath $repoRoot "ui\web\src-tauri"
$apiDir = Join-RepoPath $repoRoot "ui\api"
$apiBuildScript = Join-RepoPath $repoRoot "ui\api\scripts\build-portable.ps1"
$apiPortableDir = Join-RepoPath $apiDir "dist\$ApiOutputName"
$releaseDir = Join-RepoPath $tauriDir "target\release"
$releaseConfig = Join-Path $releaseDir "config.toml"
$sourceConfig = Join-RepoPath $tauriDir "config.toml"
$resolvedOutputDir = Resolve-OutputPath $repoRoot $OutputDir

Assert-IsInsidePath $resolvedOutputDir $repoRoot
Assert-PathExists $webDir "Web 目录"
Assert-PathExists $tauriDir "Tauri 目录"
Assert-PathExists $apiBuildScript "API 构建脚本"

Write-Step "构建 Tauri 桌面端"
Write-Info "Web 目录: $webDir"

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "未找到 cargo，请先安装 Rust 工具链。"
}

Push-Location $webDir
try {
    $tauriBuildStartedAt = Get-Date
    Invoke-ExternalCommand "Tauri 构建失败" {
        cargo tauri build --no-bundle
    }
}
finally {
    Pop-Location
}

$desktopExe = Get-LatestReleaseExe $releaseDir $tauriBuildStartedAt

Write-Step "构建 API 便携包"
Write-Info "API 构建脚本: $apiBuildScript"

Invoke-ExternalCommand "API 便携包构建失败" {
    & $apiBuildScript -OutputName $ApiOutputName -PythonVersion $PythonVersion
}

Assert-PathExists $apiPortableDir "API 便携包输出目录"

Write-Step "汇总发布文件"
Write-Info "输出目录: $resolvedOutputDir"

if (Test-Path -LiteralPath $resolvedOutputDir) {
    Remove-Item -LiteralPath $resolvedOutputDir -Recurse -Force
}

New-Item -ItemType Directory -Path $resolvedOutputDir -Force | Out-Null

Write-Info "复制桌面端: $desktopExe"
Copy-Item -LiteralPath $desktopExe -Destination $resolvedOutputDir -Force

if (Test-Path -LiteralPath $releaseConfig) {
    Write-Info "复制配置文件: $releaseConfig"
    Copy-Item -LiteralPath $releaseConfig -Destination $resolvedOutputDir -Force
}
else {
    Assert-PathExists $sourceConfig "Tauri 配置文件"
    Write-Info "复制配置文件: $sourceConfig"
    Copy-Item -LiteralPath $sourceConfig -Destination $resolvedOutputDir -Force
}

Write-Info "复制 API 便携包: $apiPortableDir"
Copy-DirectoryContents $apiPortableDir $resolvedOutputDir

$totalSize = (Get-ChildItem -LiteralPath $resolvedOutputDir -Recurse -Force | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Step "构建完成"
Write-Info "发布目录: $resolvedOutputDir"
Write-Info "总大小: $([Math]::Round($totalSize, 2)) MB"
