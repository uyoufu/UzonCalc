<#
.SYNOPSIS
    Build and upload template.js to the production server.

.DESCRIPTION
    Builds src/core/uzoncalc/template/js/dist/template.js, then uses scp to copy it
    to the remote server at /var/www/uzoncalc/scripts/.

.EXAMPLE
    .\upload-template-js.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$server = "root@calc.uzoncloud.com"
$remotePath = "/var/www/uzoncalc/scripts/template.js"

$scriptDir = Split-Path -Path $PSCommandPath -Parent
$projectRoot = Split-Path -Path $scriptDir -Parent
# 模板脚本源码位于核心包目录。
$templateJsDir = Join-Path $projectRoot "src/core/uzoncalc/template/js"
$localPath = Join-Path $projectRoot "src/core/uzoncalc/template/js/dist/template.js"

if (-not (Test-Path $templateJsDir)) {
    Write-Host "ERROR: Template JS directory not found: $templateJsDir" -ForegroundColor Red
    exit 1
}

Write-Host "Building template.js ..."
Push-Location $templateJsDir
try {
    # 上传前先编译，确保远端使用最新模板脚本。
    bun run build
    $buildExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($buildExitCode -ne 0) {
    Write-Host "Build failed with exit code $buildExitCode" -ForegroundColor Red
    exit $buildExitCode
}

if (-not (Test-Path $localPath)) {
    Write-Host "ERROR: Local file not found: $localPath" -ForegroundColor Red
    exit 1
}

Write-Host "Uploading template.js to $server`:$remotePath ..."
scp $localPath "$server`:$remotePath"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload successful." -ForegroundColor Green
} else {
    Write-Host "Upload failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
