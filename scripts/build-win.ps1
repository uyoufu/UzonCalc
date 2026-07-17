<#
.SYNOPSIS
    Build the Windows desktop package.

.DESCRIPTION
    Builds the Tauri desktop executable and the API portable package, then
    combines both outputs into dist\uzoncalc-win-x64-<app-version>.
#>

[CmdletBinding()]
param(
    [string]$OutputDir,
    [string]$ApiOutputName = "UzonCalc-Portable",
    [string]$PythonVersion = "3.13.14",
    [string]$PythonCacheRoot
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
        [string]$Path,
        [string]$Version
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return (Join-RepoPath $Root "dist\uzoncalc-win-x64-$Version")
    }

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return (Join-RepoPath $Root $Path)
}

function Get-CargoPackageVersion {
    param([string]$ManifestPath)

    Assert-PathExists $ManifestPath "Rust 项目 Cargo.toml"

    $inPackageSection = $false

    foreach ($line in Get-Content -LiteralPath $ManifestPath) {
        if ($line -match '^\s*\[(.+)\]\s*$') {
            $inPackageSection = ($Matches[1] -eq "package")
            continue
        }

        if ($inPackageSection -and $line -match '^\s*version\s*=\s*"([^"]+)"\s*$') {
            return $Matches[1]
        }
    }

    throw "未找到 Rust 项目版本号: $ManifestPath"
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

function Resolve-ArchivePath {
    param([string]$OutputDirectory)

    $parentDirectory = Split-Path -Path $OutputDirectory -Parent
    $leafName = Split-Path -Path $OutputDirectory -Leaf

    return (Join-Path $parentDirectory "$leafName.zip")
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

# 目录重构后，桌面端与 API 均位于 src 目录下。
$webDir = Join-RepoPath $repoRoot "src\web"
$tauriDir = Join-RepoPath $repoRoot "src\web\src-tauri"
$nodeModulesDir = Join-RepoPath $webDir "node_modules"
$iconIcoPath = Join-RepoPath $tauriDir "icons\icon.ico"
$iconSourcePath = Join-RepoPath $webDir "public\icons\favicon.svg"
$apiDir = Join-RepoPath $repoRoot "src\api"
$apiBuildScript = Join-RepoPath $repoRoot "src\api\scripts\build-portable.ps1"
$apiPortableDir = Join-RepoPath $apiDir "dist\$ApiOutputName"
$releaseDir = Join-RepoPath $tauriDir "target\release"
$releaseConfig = Join-Path $releaseDir "config.toml"
$sourceConfig = Join-RepoPath $tauriDir "config.toml"
$cargoManifest = Join-RepoPath $tauriDir "Cargo.toml"
$appVersion = Get-CargoPackageVersion $cargoManifest
$resolvedOutputDir = Resolve-OutputPath $repoRoot $OutputDir $appVersion
$archivePath = Resolve-ArchivePath $resolvedOutputDir

Assert-IsInsidePath $resolvedOutputDir $repoRoot
Assert-IsInsidePath $archivePath $repoRoot
Assert-PathExists $webDir "Web 目录"
Assert-PathExists $tauriDir "Tauri 目录"
Assert-PathExists $apiBuildScript "API 构建脚本"

Write-Step "准备 Tauri 桌面端"
Write-Info "Web 目录: $webDir"

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "未找到 cargo，请先安装 Rust 工具链。"
}

if (-not (Test-Path -LiteralPath $nodeModulesDir)) {
    if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
        throw "未找到 bun，请先安装 Bun。"
    }

    Write-Info "未找到 node_modules，开始安装 Web 依赖。"
    Push-Location $webDir
    try {
        Invoke-ExternalCommand "Web 依赖安装失败" {
            bun install
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Info "已找到 node_modules，跳过 Web 依赖安装。"
}

if (-not (Test-Path -LiteralPath $iconIcoPath)) {
    Assert-PathExists $iconSourcePath "Tauri 图标源文件"

    Write-Info "未找到 icon.ico，开始生成 Tauri 图标。"
    Push-Location $tauriDir
    try {
        Invoke-ExternalCommand "Tauri 图标生成失败" {
            cargo tauri icon ..\public\icons\favicon.svg
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Info "已找到 icon.ico，跳过 Tauri 图标生成。"
}

Write-Step "构建 Tauri 桌面端"

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

$apiBuildArgs = @{
    OutputName = $ApiOutputName
    PythonVersion = $PythonVersion
}

if (-not [string]::IsNullOrWhiteSpace($PythonCacheRoot)) {
    $apiBuildArgs.PythonCacheRoot = $PythonCacheRoot
}

Invoke-ExternalCommand "API 便携包构建失败" {
    & $apiBuildScript @apiBuildArgs
}

Assert-PathExists $apiPortableDir "API 便携包输出目录"

Write-Step "汇总整包文件"
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

Write-Step "打包 zip 文件"
Write-Info "zip 文件: $archivePath"

if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

$archiveParent = Split-Path -Path $archivePath -Parent
Push-Location $archiveParent
try {
    Compress-Archive -Path (Split-Path -Path $resolvedOutputDir -Leaf) -DestinationPath $archivePath
}
finally {
    Pop-Location
}

$archiveSize = (Get-Item -LiteralPath $archivePath).Length / 1MB

Write-Step "上传 zip 文件"
$onedoCommand = Get-Command onedo -ErrorAction SilentlyContinue
if ($onedoCommand) {
    Write-Info "检测到 onedo，开始上传: $archivePath"
    Invoke-ExternalCommand "zip 文件上传失败" {
        onedo minio soft -p $archivePath
    }
    Write-Info "zip 文件上传完成。"
}
else {
    Write-Info "未找到 onedo，跳过上传。"
}

Write-Step "构建完成"
Write-Info "整包目录: $resolvedOutputDir"
Write-Info "总大小: $([Math]::Round($totalSize, 2)) MB"
Write-Info "zip 文件: $archivePath"
Write-Info "zip 大小: $([Math]::Round($archiveSize, 2)) MB"
