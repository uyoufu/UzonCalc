<#
.SYNOPSIS
    Upload template.js to the production server.

.DESCRIPTION
    Uses scp to copy uzoncalc/template/js/dist/template.js to the remote server
    at /var/www/uzoncalc/scripts/.

.EXAMPLE
    .\upload-template-js.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$server = "root@69.63.204.155"
$remotePath = "/var/www/uzoncalc/scripts/template.js"

$scriptDir = Split-Path -Path $PSCommandPath -Parent
$projectRoot = Split-Path -Path $scriptDir -Parent
$localPath = Join-Path $projectRoot "uzoncalc/template/js/dist/template.js"

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
