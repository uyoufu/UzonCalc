Set-StrictMode -Version Latest

function Get-DeployConfig {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $repoRoot = Split-Path -Parent $scriptDir
    $uiRoot = Join-Path $repoRoot "ui"
    $desktopMauiRoot = Join-Path $uiRoot "desktop-maui"
    $cacheRoot = Join-Path $repoRoot ".cache\desktop-maui\python"

    return @{
        RepoRoot = $repoRoot
        DesktopMauiRoot = $desktopMauiRoot
        MauiProjectFile = Join-Path $desktopMauiRoot "src\UzoncalcMaui.csproj"
        ApiRoot = Join-Path $uiRoot "api"
        Configuration = "Release"
        Framework = "net10.0-windows10.0.19041.0"
        RuntimeIdentifier = "win-x64"
        SatelliteResourceLanguages = "zh-Hans;zh-Hant;en"
        PythonVersion = "3.11.9"
        PythonCacheRoot = $cacheRoot
        PublishRoot = Join-Path $repoRoot "publish\win"
    }
}
