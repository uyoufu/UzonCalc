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
$EMBED_DIR = Join-Path $PROJECT_ROOT $TargetDir

if ([string]::IsNullOrWhiteSpace($CacheRoot)) {
    $CacheRoot = Join-Path $REPO_ROOT ".cache\desktop-maui\python"
} elseif (-not [System.IO.Path]::IsPathRooted($CacheRoot)) {
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

# ============================================
# 1. 下载嵌入式 Python
# ============================================

Write-Info "开始设置嵌入式 Python 环境..."

# 确定下载 URL（根据系统架构）
$arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
$downloadUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-$arch.zip"
$zipFile = Join-Path $env:TEMP "python-embedded.zip"
$requirementsFile = Join-Path $PROJECT_ROOT "requirements.txt"
$requirementsHash = "no-requirements"
if (Test-Path -LiteralPath $requirementsFile) {
    $requirementsHash = (Get-FileHash -LiteralPath $requirementsFile -Algorithm SHA256).Hash.ToLowerInvariant()
}

$cacheKey = "v1-$PythonVersion-$arch-$requirementsHash"
$cacheDir = Join-Path $CacheRoot $cacheKey
$cachePythonExe = Join-Path $cacheDir "python.exe"

Write-Info "Python cache root: $CacheRoot"
Write-Info "Python cache key: $cacheKey"

if (Test-Path -LiteralPath $cachePythonExe) {
    Write-Info "检测到缓存的嵌入式 Python 环境，直接复制到目标目录..."
    Remove-DirectoryIfExists -Path $EMBED_DIR
    Copy-DirectoryContents -Source $cacheDir -Destination $EMBED_DIR

    $pythonExe = Join-Path $EMBED_DIR "python.exe"
    Write-Info "========================================="
    Write-Info "嵌入式 Python 环境设置完成（来自缓存）！"
    Write-Info "========================================="
    Write-Host ""
    Write-Host "Python 路径: $EMBED_DIR" -ForegroundColor Cyan
    Write-Host "Python 可执行文件: $pythonExe" -ForegroundColor Cyan
    Write-Host ""
    return
}

Write-Info "下载 Python $PythonVersion ($arch)..."
Write-Host "  URL: $downloadUrl"

try {
    # 使用 .NET 下载（更可靠）
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $zipFile)
    Write-Info "下载完成"
} catch {
    Write-Error-Message "下载失败: $_"
    Write-Host "请手动下载并解压到: $EMBED_DIR"
    Write-Host "下载地址: $downloadUrl"
    exit 1
}

# ============================================
# 2. 解压到目标目录
# ============================================

Write-Info "解压 Python 到 $EMBED_DIR..."

if (Test-Path $EMBED_DIR) {
    Write-Info "目标目录已存在，将覆盖..."
    Remove-DirectoryIfExists -Path $EMBED_DIR
}

Expand-Archive -Path $zipFile -DestinationPath $EMBED_DIR -Force
Remove-Item $zipFile

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

Write-Info "安装 pip..."

$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipFile = Join-Path $env:TEMP "get-pip.py"

try {
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($getPipUrl, $getPipFile)
    
    # 使用嵌入式 Python 安装 pip
    $pythonExe = Join-Path $EMBED_DIR "python.exe"
    & $pythonExe $getPipFile --no-warn-script-location
    Assert-LastCommandSucceeded -Message "pip 安装命令执行失败。"
    
    Remove-Item $getPipFile
    Write-Info "pip 安装成功"
} catch {
    Write-Error-Message "pip 安装失败: $_"
    throw
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

Write-Info "安装项目依赖..."

$pythonExe = Join-Path $EMBED_DIR "python.exe"
$pipExe = Join-Path $EMBED_DIR "Scripts\pip.exe"

if (Test-Path $requirementsFile) {
    if (Test-Path $pipExe) {
        & $pipExe install -r $requirementsFile --no-warn-script-location
        Assert-LastCommandSucceeded -Message "项目依赖安装命令执行失败。"
        Write-Info "依赖安装完成"
    } else {
        throw "pip.exe 未找到，无法安装项目依赖。"
    }
} else {
    Write-Host "  未找到 requirements.txt，跳过依赖安装" -ForegroundColor Yellow
}

# ============================================
# 7. 写入缓存
# ============================================

Write-Info "写入嵌入式 Python 缓存..."
Ensure-Directory -Path $CacheRoot
Remove-DirectoryIfExists -Path $cacheDir
Copy-DirectoryContents -Source $EMBED_DIR -Destination $cacheDir
Write-Info "缓存完成: $cacheDir"

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
