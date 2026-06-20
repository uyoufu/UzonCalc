<#
.SYNOPSIS
    Render decorated examples and publish output HTML files to the production server.

.DESCRIPTION
    1. Recursively finds Python examples decorated with @uzon_calc in examples/.
    2. Renders each calculation document to a temporary publish directory.
    3. Packages the generated HTML files into a zip archive, preserving relative paths.
    4. Uploads the archive to the remote server via scp.
    5. Extracts the archive on the remote server via ssh and removes temporary files.

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
$archiveName = "examples-output.zip"
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "uzoncalc-publish-examples-$([guid]::NewGuid().ToString('N'))"
$publishOutputDir = Join-Path $tempRoot "html"
$archivePath = Join-Path $tempRoot $archiveName

function Test-UzonCalcExample {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    # 使用 Python AST 检测真实函数装饰器，避免匹配文档字符串中的示例代码。
    $checkScript = @"
import ast
import pathlib
import sys

source_path = pathlib.Path(sys.argv[1])
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id == "uzon_calc":
            sys.exit(0)
sys.exit(1)
"@

    uv run --no-project python -c $checkScript $Path
    return $LASTEXITCODE -eq 0
}

try {
    # --- Step 1: Render decorated example scripts ---
    Write-Host "=== Rendering example scripts ===" -ForegroundColor Cyan

    if (-not (Test-Path $examplesDir)) {
        Write-Host "ERROR: Examples directory not found: $examplesDir" -ForegroundColor Red
        exit 1
    }

    New-Item -ItemType Directory -Path $publishOutputDir -Force | Out-Null

    $exampleFiles = Get-ChildItem -Path $examplesDir -Filter "*.py" -File -Recurse | Where-Object {
        $_.Name -ne "__init__.py" -and (Test-UzonCalcExample -Path $_.FullName)
    } | Sort-Object FullName

    if ($exampleFiles.Count -eq 0) {
        Write-Host "ERROR: No @uzon_calc example scripts found in $examplesDir" -ForegroundColor Red
        exit 1
    }

    foreach ($file in $exampleFiles) {
        $relativePath = [System.IO.Path]::GetRelativePath($examplesDir, $file.FullName)
        $relativeBase = [System.IO.Path]::ChangeExtension($relativePath, $null)
        $outputPath = Join-Path $publishOutputDir "$relativeBase.html"
        $outputParent = Split-Path -Path $outputPath -Parent

        if (-not (Test-Path $outputParent)) {
            New-Item -ItemType Directory -Path $outputParent -Force | Out-Null
        }

        Write-Host "Rendering: $relativePath -> $([System.IO.Path]::GetRelativePath($publishOutputDir, $outputPath))" -ForegroundColor Yellow
        uv run --project $projectRoot --package uzoncalc uzoncalc $file.FullName --output $outputPath
        $renderExitCode = $LASTEXITCODE
        if ($renderExitCode -ne 0) {
            Write-Host "ERROR: Failed to render $relativePath with exit code $renderExitCode" -ForegroundColor Red
            exit $renderExitCode
        }
    }

    # --- Step 2: Package output HTML files ---
    Write-Host ""
    Write-Host "=== Packaging output files ===" -ForegroundColor Cyan

    $htmlFiles = Get-ChildItem -Path $publishOutputDir -Filter "*.html" -File -Recurse
    if ($htmlFiles.Count -eq 0) {
        Write-Host "ERROR: No HTML files generated in $publishOutputDir" -ForegroundColor Red
        exit 1
    }

    Write-Host "Found $($htmlFiles.Count) HTML file(s):"
    $htmlFiles | ForEach-Object {
        Write-Host "  $([System.IO.Path]::GetRelativePath($publishOutputDir, $_.FullName))"
    }

    Compress-Archive -Path (Join-Path $publishOutputDir "*") -DestinationPath $archivePath
    Write-Host "Archive created: $archivePath" -ForegroundColor Green

    # --- Step 3: Upload to server ---
    Write-Host ""
    Write-Host "=== Uploading to $server`:$remotePath ===" -ForegroundColor Cyan

    ssh $server "mkdir -p $remotePath"
    $sshExitCode = $LASTEXITCODE
    if ($sshExitCode -ne 0) {
        Write-Host "ERROR: Failed to ensure remote directory with exit code $sshExitCode" -ForegroundColor Red
        exit $sshExitCode
    }

    Write-Host "Uploading $archiveName ..."
    scp $archivePath "${server}:${remotePath}/${archiveName}"
    $scpExitCode = $LASTEXITCODE

    if ($scpExitCode -ne 0) {
        Write-Host "ERROR: Upload failed with exit code $scpExitCode" -ForegroundColor Red
        exit $scpExitCode
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

    $extractExitCode = $LASTEXITCODE
    if ($extractExitCode -ne 0) {
        Write-Host "ERROR: Extraction failed with exit code $extractExitCode" -ForegroundColor Red
        exit $extractExitCode
    }

    Write-Host ""
    Write-Host "=== Publish complete ===" -ForegroundColor Green
    Write-Host "Examples published to ${server}:${remotePath}/"
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item $tempRoot -Recurse -Force
        Write-Host "Temporary files removed: $tempRoot" -ForegroundColor DarkGray
    }
}
