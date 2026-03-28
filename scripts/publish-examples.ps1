<#
.SYNOPSIS
    Run all examples and publish output HTML files to the production server.

.DESCRIPTION
    1. Runs all .py example scripts in the examples/ directory.
    2. Packages the generated HTML files from output/ into a zip archive.
    3. Uploads the archive to the remote server via scp.
    4. Extracts the archive on the remote server via ssh.

.EXAMPLE
    .\publish-examples.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$server = "root@69.63.204.155"
$remotePath = "/var/www/uzoncalc/examples"

$scriptDir = Split-Path -Path $PSCommandPath -Parent
$projectRoot = Split-Path -Path $scriptDir -Parent
$examplesDir = Join-Path $projectRoot "examples"
$outputDir = Join-Path $projectRoot "output"
$archiveName = "examples-output.zip"
$archivePath = Join-Path $outputDir $archiveName

# --- Step 1: Run all example scripts ---
Write-Host "=== Running example scripts ===" -ForegroundColor Cyan

$exampleFiles = Get-ChildItem -Path $examplesDir -Filter "*.py" -File | Where-Object {
    $_.Name -notin @('__init__.py')
}

foreach ($file in $exampleFiles) {
    Write-Host "Running: $($file.Name) ..." -ForegroundColor Yellow
    Push-Location $examplesDir
    try {
        python $file.FullName
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  WARNING: $($file.Name) exited with code $LASTEXITCODE" -ForegroundColor Red
        } else {
            Write-Host "  Done." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  ERROR running $($file.Name): $_" -ForegroundColor Red
    }
    finally {
        Pop-Location
    }
}

# --- Step 2: Package output HTML files ---
Write-Host ""
Write-Host "=== Packaging output files ===" -ForegroundColor Cyan

if (-not (Test-Path $outputDir)) {
    Write-Host "ERROR: Output directory not found: $outputDir" -ForegroundColor Red
    exit 1
}

$htmlFiles = Get-ChildItem -Path $outputDir -Filter "*.html" -File
if ($htmlFiles.Count -eq 0) {
    Write-Host "ERROR: No HTML files found in $outputDir" -ForegroundColor Red
    exit 1
}

Write-Host "Found $($htmlFiles.Count) HTML file(s):"
$htmlFiles | ForEach-Object { Write-Host "  $($_.Name)" }

# Remove old archive if exists
if (Test-Path $archivePath) {
    Remove-Item $archivePath -Force
}

# Create zip archive
Compress-Archive -Path ($htmlFiles | Select-Object -ExpandProperty FullName) -DestinationPath $archivePath
Write-Host "Archive created: $archivePath" -ForegroundColor Green

# --- Step 3: Upload to server ---
Write-Host ""
Write-Host "=== Uploading to $server`:$remotePath ===" -ForegroundColor Cyan

# Ensure remote directory exists
ssh $server "mkdir -p $remotePath"

# Upload archive
Write-Host "Uploading $archiveName ..."
scp $archivePath "${server}:${remotePath}/${archiveName}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Upload failed." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Upload successful." -ForegroundColor Green

# --- Step 4: Extract on server ---
Write-Host ""
Write-Host "=== Extracting on server ===" -ForegroundColor Cyan

ssh $server @"
    cd $remotePath &&
    unzip -o $archiveName &&
    rm -f $archiveName &&
    echo 'Extraction complete.'
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Extraction failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== Publish complete ===" -ForegroundColor Green
Write-Host "Examples published to ${server}:${remotePath}/"
