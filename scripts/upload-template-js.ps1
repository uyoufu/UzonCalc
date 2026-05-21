<#
.SYNOPSIS
    Upload template.js to the production server.

.DESCRIPTION
    Uses scp to copy src/uzoncalc/template/js/dist/template.js to the remote server
    at /var/www/uzoncalc/scripts/.

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
# 模板脚本源码随核心包迁移到 src/uzoncalc。
$localPath = Join-Path $projectRoot "src/uzoncalc/template/js/dist/template.js"

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
