# ============================================
# 嵌入式 Python 环境设置脚本
# ============================================
# 功能：下载并配置便携式 Python 环境
# 优势：无需安装，可直接打包分发
# ============================================

param(
    [string]$PythonVersion = "3.11.9",
    [string]$TargetDir = "dist\python-embedded",
    [string]$CacheRoot
)

$ErrorActionPreference = "Stop"

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$UI_ROOT = Split-Path -Parent $PROJECT_ROOT
$REPO_ROOT = Split-Path -Parent $UI_ROOT
# 核心包是 workspace 成员，安装时指向真实项目根目录。
$CORE_PROJECT_ROOT = Join-Path $REPO_ROOT "src/core"
$EMBED_DIR = Join-Path $PROJECT_ROOT $TargetDir
$pythonExe = Join-Path $EMBED_DIR "python.exe"

if ([string]::IsNullOrWhiteSpace($CacheRoot)) {
    $CacheRoot = Join-Path $REPO_ROOT ".cache\desktop-maui\python"
}
elseif (-not [System.IO.Path]::IsPathRooted($CacheRoot)) {
    $CacheRoot = Join-Path $REPO_ROOT $CacheRoot
}

function Write-Info {
    param([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Error-Message {
    param([string]$message)
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Remove-DirectoryIfExists {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Copy-DirectoryContents {
    param(
        [string]$Source,
        [string]$Destination
    )

    Ensure-Directory -Path $Destination
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
    }
}

function Assert-LastCommandSucceeded {
    param([string]$Message)

    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

function Invoke-PipInstall {
    param([string[]]$Arguments)

    & $pythonExe -m pip @Arguments --no-warn-script-location
}

function Test-PipAvailable {
    & $pythonExe -m pip --version | Out-Null
    return $LASTEXITCODE -eq 0
}

# ============================================
# 1. 下载嵌入式 Python
# ============================================

Write-Info "开始设置嵌入式 Python 环境..."

# 确定下载 URL（根据系统架构）
$arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
$downloadUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-$arch.zip"
$zipFile = Join-Path $env:TEMP "python-embedded.zip"
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipFile = Join-Path $env:TEMP "get-pip.py"
$requirementsFile = Join-Path $PROJECT_ROOT "requirements.txt"
$requirementsHash = "no-requirements"
if (Test-Path -LiteralPath $requirementsFile) {
    $requirementsHash = (Get-FileHash -LiteralPath $requirementsFile -Algorithm SHA256).Hash.ToLowerInvariant()
}

$cacheKey = "v2-$PythonVersion-$arch-$requirementsHash"
$cacheDir = Join-Path $CacheRoot $cacheKey
$cachePythonExe = Join-Path $cacheDir "python.exe"
$cacheHit = $false

Write-Info "Python cache root: $CacheRoot"
Write-Info "Python cache key: $cacheKey"

if (Test-Path -LiteralPath $cachePythonExe) {
    Write-Info "检测到缓存的嵌入式 Python 环境，复制到目标目录..."
    Remove-DirectoryIfExists -Path $EMBED_DIR
    Copy-DirectoryContents -Source $cacheDir -Destination $EMBED_DIR

    $pythonExe = Join-Path $EMBED_DIR "python.exe"
    $cacheHit = $true
    Write-Info "缓存环境复制完成，将继续刷新本地 workspace 包。"
}

$downloadedPython = $false

if ($cacheHit) {
    Write-Info "使用缓存的嵌入式 Python，跳过下载和解压。"
}
elseif (Test-Path $pythonExe) {
    Write-Info "检测到已缓存的嵌入式 Python: $EMBED_DIR"
    Write-Info "跳过下载和解压，继续检查配置并安装依赖..."
}
else {
    Write-Info "下载 Python $PythonVersion ($arch)..."
    Write-Host "  URL: $downloadUrl"

    try {
        # 使用 .NET 下载（更可靠）
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($downloadUrl, $zipFile)
        $downloadedPython = $true
        Write-Info "下载完成"
    }
    catch {
        Write-Error-Message "下载失败: $_"
        Write-Host "请手动下载并解压到: $EMBED_DIR"
        Write-Host "下载地址: $downloadUrl"
        throw
    }
}

# ============================================
# 2. 解压到目标目录
# ============================================

Write-Info "解压 Python 到 $EMBED_DIR..."

if ($downloadedPython) {
    if (Test-Path $EMBED_DIR) {
        Write-Info "目标目录已存在，将覆盖..."
        Remove-DirectoryIfExists -Path $EMBED_DIR
    }

    Ensure-Directory -Path $EMBED_DIR
    Expand-Archive -LiteralPath $zipFile -DestinationPath $EMBED_DIR -Force

    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw "Python 解压失败，未找到: $pythonExe"
    }
}
else {
    Write-Info "未下载新的 Python，跳过解压。"
}

# ============================================
# 3. 启用标准库（重要！）
# ============================================

Write-Info "配置 Python 环境..."

# 找到 pythonXX._pth 文件并修改，以启用 site-packages
$pthFile = Get-ChildItem -Path $EMBED_DIR -Filter "python*._pth" | Select-Object -First 1

if ($pthFile) {
    $pthPath = $pthFile.FullName
    Write-Info "修改 $($pthFile.Name) 以启用 site-packages..."
    
    # 读取内容
    $content = Get-Content $pthPath
    
    # 取消注释 import site（如果被注释）
    $newContent = $content -replace '#import site', 'import site'
    
    # 如果没有 import site，添加它
    if ($newContent -notcontains 'import site') {
        $newContent += 'import site'
    }
    
    # 添加 Lib\site-packages
    if ($newContent -notcontains 'Lib\site-packages') {
        $newContent += 'Lib\site-packages'
    }
    
    # 写回文件
    $newContent | Set-Content $pthPath -Encoding ASCII
    Write-Info "配置完成"
}

# ============================================
# 4. 下载并安装 pip
# ============================================

Write-Info "检查 pip..."

if (Test-PipAvailable) {
    Write-Info "pip 模块可用，跳过 pip 安装"
}
else {
    Write-Info "安装 pip..."

    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($getPipUrl, $getPipFile)
        
        # 使用嵌入式 Python 安装 pip
        $pythonExe = Join-Path $EMBED_DIR "python.exe"
        & $pythonExe $getPipFile --no-warn-script-location
        Assert-LastCommandSucceeded -Message "pip 安装命令执行失败。"

        if (-not (Test-PipAvailable)) {
            throw "pip 安装后仍无法通过 python -m pip 运行。"
        }
        
        Remove-Item $getPipFile
        Write-Info "pip 安装成功"
    }
    catch {
        Write-Error-Message "pip 安装失败: $_"
        throw
    }
}

# ============================================
# 5. 创建 Lib\site-packages 目录
# ============================================

$libDir = Join-Path $EMBED_DIR "Lib"
$sitePackages = Join-Path $libDir "site-packages"

if (-not (Test-Path $libDir)) {
    New-Item -ItemType Directory -Path $libDir | Out-Null
}
if (-not (Test-Path $sitePackages)) {
    New-Item -ItemType Directory -Path $sitePackages | Out-Null
}

# ============================================
# 6. 安装依赖
# ============================================

Write-Info "安装第三方依赖..."

$pythonExe = Join-Path $EMBED_DIR "python.exe"
$requirementsFile = Join-Path $PROJECT_ROOT "requirements.txt"

if ($cacheHit) {
    Write-Info "使用缓存环境，跳过第三方依赖安装。"
}
elseif (Test-Path $requirementsFile) {
    $filteredRequirementsFile = Join-Path $env:TEMP "uzoncalc-api-requirements.txt"
    $requirementsContent = Get-Content -LiteralPath $requirementsFile |
        Where-Object {
            $_ -notmatch '^\s*-e\s+file:' -and
            $_ -notmatch '^\s*uzoncalc\s*(?:[#;].*)?$'
        }

    $requirementsContent | Set-Content -LiteralPath $filteredRequirementsFile -Encoding UTF8

    try {
        Invoke-PipInstall -Arguments @("install", "-r", $filteredRequirementsFile)
        Assert-LastCommandSucceeded -Message "依赖安装命令执行失败。"
    }
    catch {
        Write-Error-Message "依赖安装失败: $_"
        throw
    }
    finally {
        if (Test-Path -LiteralPath $filteredRequirementsFile) {
            Remove-Item -LiteralPath $filteredRequirementsFile -Force
        }
    }

    Write-Info "依赖安装完成"
}
else {
    Write-Host "  未找到 requirements.txt，跳过依赖安装" -ForegroundColor Yellow
}

# ============================================
# 7. 写入缓存
# ============================================

if ($cacheHit) {
    Write-Info "当前环境来自缓存，跳过缓存写入。"
}
else {
    Write-Info "写入嵌入式 Python 缓存..."
    Ensure-Directory -Path $CacheRoot
    Remove-DirectoryIfExists -Path $cacheDir
    Copy-DirectoryContents -Source $EMBED_DIR -Destination $cacheDir
    Write-Info "缓存完成: $cacheDir"
}

# ============================================
# 8. 安装本地 workspace 包
# ============================================

Write-Info "安装本地 workspace 包..."

try {
    Invoke-PipInstall -Arguments @("install", "--no-build-isolation", "--no-deps", "--force-reinstall", $CORE_PROJECT_ROOT)
    Assert-LastCommandSucceeded -Message "uzoncalc 安装命令执行失败。"

    Invoke-PipInstall -Arguments @("install", "--no-build-isolation", "--no-deps", "--force-reinstall", $PROJECT_ROOT)
    Assert-LastCommandSucceeded -Message "uzoncalc-api 安装命令执行失败。"
}
catch {
    Write-Error-Message "本地 workspace 包安装失败: $_"
    throw
}

Write-Info "已安装的本地包版本:"
& $pythonExe -m pip show uzoncalc uzoncalc-api
Assert-LastCommandSucceeded -Message "本地包版本检查失败。"

# ============================================
# 完成
# ============================================

Write-Info "========================================="
Write-Info "嵌入式 Python 环境设置完成！"
Write-Info "========================================="
Write-Host ""
Write-Host "Python 路径: $EMBED_DIR" -ForegroundColor Cyan
Write-Host "Python 可执行文件: $pythonExe" -ForegroundColor Cyan
Write-Host ""
Write-Info "后续步骤："
Write-Host "  1. 测试 Python: $pythonExe --version"
Write-Host "  2. 运行应用: $pythonExe main.py"
Write-Host "  3. 分发时，保留 dist 目录中的嵌入式 Python 环境"
Write-Host ""
