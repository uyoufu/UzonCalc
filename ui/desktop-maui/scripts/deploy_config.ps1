Set-StrictMode -Version Latest

function Get-DeployConfig {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $desktopMauiRoot = Split-Path -Parent $scriptDir
    $uiRoot = Split-Path -Parent $desktopMauiRoot
    $repoRoot = Split-Path -Parent $uiRoot

    return @{
        RepoRoot = $repoRoot
        DesktopMauiRoot = $desktopMauiRoot
        ApiRoot = Join-Path $uiRoot "api"
        Configuration = "Release"
        Framework = "net10.0-windows10.0.19041.0"
        RuntimeIdentifier = ""
        PythonVersion = "3.11.9"
        PublishRoot = Join-Path $repoRoot "publish\win"
    }
}
