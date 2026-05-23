# ============================================
# 便携式打包脚本
# ============================================
# 功能：创建可分发的便携式应用包
# 不使用 PyInstaller，而是打包完整的运行环境
# ============================================

param(
    [string]$OutputName = "UzonCalc-Portable",
    [string]$PythonVersion = "3.11.9",
    [string]$PythonCacheRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-FullPath {
    param([string]$Path)

    return [System.IO.Path]::GetFullPath($Path)
}

function Assert-PathIsInside {
    param(
        [string]$Path,
        [string]$ParentPath,
        [string]$Description
    )

    $fullPath = Resolve-FullPath $Path
    $fullParentPath = (Resolve-FullPath $ParentPath).TrimEnd('\', '/')

    if (-not $fullPath.StartsWith($fullParentPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Description 必须位于 $fullParentPath 内: $fullPath"
    }
}

function Assert-PathsAreSeparate {
    param(
        [string]$FirstPath,
        [string]$SecondPath,
        [string]$Description
    )

    $first = (Resolve-FullPath $FirstPath).TrimEnd('\', '/')
    $second = (Resolve-FullPath $SecondPath).TrimEnd('\', '/')

    if ($first.Equals($second, [System.StringComparison]::OrdinalIgnoreCase) -or
        $first.StartsWith($second + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase) -or
        $second.StartsWith($first + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Description 不能互相包含: $first <-> $second"
    }
}

function Test-InvalidOutputName {
    param([string]$Name)

    return [string]::IsNullOrWhiteSpace($Name) -or
        [System.IO.Path]::IsPathRooted($Name) -or
        $Name.IndexOfAny([System.IO.Path]::GetInvalidFileNameChars()) -ge 0 -or
        $Name.Contains('\') -or
        $Name.Contains('/') -or
        $Name -eq "." -or
        $Name -eq ".."
}

# 路径配置
$SCRIPT_DIR = Resolve-FullPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PROJECT_ROOT = Resolve-FullPath (Split-Path -Parent $SCRIPT_DIR)
$DIST_DIR = Resolve-FullPath (Join-Path $PROJECT_ROOT "dist")
$EMBEDDED_PYTHON_RELATIVE_DIR = "dist\python-embedded"
$EMBEDDED_PYTHON_SOURCE_DIR = Resolve-FullPath (Join-Path $PROJECT_ROOT $EMBEDDED_PYTHON_RELATIVE_DIR)

if (Test-InvalidOutputName -Name $OutputName) {
    throw "OutputName 只能是 dist 下的单级目录名: $OutputName"
}

$OUTPUT_DIR = Resolve-FullPath (Join-Path $DIST_DIR $OutputName)
$EMBEDDED_PYTHON_OUTPUT_DIR = Resolve-FullPath (Join-Path $OUTPUT_DIR $EMBEDDED_PYTHON_RELATIVE_DIR)

Assert-PathIsInside -Path $OUTPUT_DIR -ParentPath $DIST_DIR -Description "输出目录"
Assert-PathsAreSeparate -FirstPath $OUTPUT_DIR -SecondPath $EMBEDDED_PYTHON_SOURCE_DIR -Description "输出目录和嵌入式 Python 源目录"

function Write-Info {
    param([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Step {
    param([string]$message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

# ============================================
# 步骤 1: 设置嵌入式 Python
# ============================================

Write-Step "步骤 1: 设置嵌入式 Python 环境"

$setupScript = Join-Path $SCRIPT_DIR "setup-embedded-python.ps1"
if (Test-Path -LiteralPath $setupScript) {
    $setupArgs = @{
        PythonVersion = $PythonVersion
        TargetDir = $EMBEDDED_PYTHON_RELATIVE_DIR
    }

    if (-not [string]::IsNullOrWhiteSpace($PythonCacheRoot)) {
        $setupArgs.CacheRoot = $PythonCacheRoot
    }

    & $setupScript @setupArgs
}
else {
    Write-Error "未找到 setup-embedded-python.ps1"
    exit 1
}

# ============================================
# 步骤 2: 创建输出目录
# ============================================

Write-Step "步骤 2: 创建输出目录"

if (Test-Path -LiteralPath $OUTPUT_DIR) {
    Write-Info "清理旧的输出目录..."
    Remove-Item -LiteralPath $OUTPUT_DIR -Recurse -Force
}

New-Item -ItemType Directory -Path $OUTPUT_DIR | Out-Null
Write-Info "输出目录: $OUTPUT_DIR"

# ============================================
# 步骤 3: 复制必要文件
# ============================================

Write-Step "步骤 3: 复制项目文件"

# 要复制的目录和文件
$itemsToCopy = @(
    "app",
    "config",
    "utils",
    "main.py",
    "requirements.txt"
)

foreach ($item in $itemsToCopy) {
    $sourcePath = Join-Path $PROJECT_ROOT $item
    if (Test-Path -LiteralPath $sourcePath) {
        Write-Info "复制: $item"
        
        if (Test-Path -LiteralPath $sourcePath -PathType Container) {
            # 目录
            Copy-Item -LiteralPath $sourcePath -Destination $OUTPUT_DIR -Recurse -Force
        }
        else {
            # 文件
            Copy-Item -LiteralPath $sourcePath -Destination $OUTPUT_DIR -Force
        }
    }
    else {
        Write-Host "  跳过（不存在）: $item" -ForegroundColor Yellow
    }
}

if (Test-Path -LiteralPath $EMBEDDED_PYTHON_SOURCE_DIR) {
    $embeddedPythonOutputParent = Split-Path -Parent $EMBEDDED_PYTHON_OUTPUT_DIR
    if (-not (Test-Path -LiteralPath $embeddedPythonOutputParent)) {
        New-Item -ItemType Directory -Path $embeddedPythonOutputParent -Force | Out-Null
    }

    Write-Info "复制: $EMBEDDED_PYTHON_RELATIVE_DIR"
    Copy-Item -LiteralPath $EMBEDDED_PYTHON_SOURCE_DIR -Destination $embeddedPythonOutputParent -Recurse -Force
}
else {
    Write-Host "  跳过（不存在）: $EMBEDDED_PYTHON_RELATIVE_DIR" -ForegroundColor Yellow
}

# ============================================
# 步骤 3.1: 设置便携包运行环境
# ============================================

$portableConfigDir = Join-Path $OUTPUT_DIR "config"
if (Test-Path -LiteralPath $portableConfigDir) {
    Write-Info "设置便携包运行环境: prod"

    $portableEnvPath = Join-Path $portableConfigDir ".env"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($portableEnvPath, "prod", $utf8NoBom)

    $portableDevConfig = Join-Path $portableConfigDir "app.dev.ini"
    if (Test-Path -LiteralPath $portableDevConfig) {
        Write-Info "移除开发环境配置: config\app.dev.ini"
        Remove-Item -LiteralPath $portableDevConfig -Force
    }
}
else {
    Write-Host "  跳过（不存在）: config" -ForegroundColor Yellow
}

$portableDataDirs = @(
    "data\db",
    "data\public",
    "data\www",
    "data\calcs"
)

foreach ($dataDir in $portableDataDirs) {
    $portableDataDir = Join-Path $OUTPUT_DIR $dataDir
    if (-not (Test-Path -LiteralPath $portableDataDir)) {
        New-Item -ItemType Directory -Path $portableDataDir -Force | Out-Null
    }
}

# ============================================
# 步骤 4: 创建启动脚本
# ============================================

Write-Step "步骤 4: 创建启动脚本"

# PowerShell 启动脚本（更强大）
$startPs1 = @"
# UzonCalc API 后台服务启动脚本
`$ErrorActionPreference = "Stop"

`$apiHost = "127.0.0.1"
`$apiPort = 3345

# 切换到脚本所在目录
Set-Location `$PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UzonCalc API 后台服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查嵌入式 Python
`$pythonExe = Join-Path `$PSScriptRoot "dist\python-embedded\python.exe"
if (-not (Test-Path `$pythonExe)) {
    Write-Host "[错误] 未找到 Python: `$pythonExe" -ForegroundColor Red
    pause
    exit 1
}

`$mainPy = Join-Path `$PSScriptRoot "main.py"
if (-not (Test-Path `$mainPy)) {
    Write-Host "[错误] 未找到入口文件: `$mainPy" -ForegroundColor Red
    pause
    exit 1
}

`$logDir = Join-Path `$PSScriptRoot "logs"
if (-not (Test-Path `$logDir)) {
    New-Item -ItemType Directory -Path `$logDir -Force | Out-Null
}

`$logPath = Join-Path `$logDir "uzoncalc.log"
try {
    `$logStream = [System.IO.File]::Open(`$logPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    `$logStream.Close()
}
catch {
    Write-Host "[错误] 日志文件不可写: `$logPath" -ForegroundColor Red
    Write-Host "可能已有残留 Python 服务正在占用日志文件，请先关闭后重试。" -ForegroundColor Yellow
    Write-Host "详细信息: `$(`$_.Exception.Message)" -ForegroundColor Yellow
    pause
    exit 1
}

`$listenerPid = `$null
if (Get-Command -Name Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    `$listener = Get-NetTCPConnection -LocalPort `$apiPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (`$listener) {
        `$listenerPid = `$listener.OwningProcess
    }
}

if (-not `$listenerPid) {
    `$netstatPattern = "^\s*TCP\s+\S+:`$apiPort\s+\S+\s+LISTENING\s+(\d+)\s*`$"
    `$netstatLine = netstat -ano | Select-String -Pattern `$netstatPattern | Select-Object -First 1
    if (`$netstatLine -and `$netstatLine.Line -match `$netstatPattern) {
        `$listenerPid = `$matches[1]
    }
}

if (`$listenerPid) {
    Write-Host "[错误] 端口 `$apiPort 已被占用，PID: `$listenerPid" -ForegroundColor Red
    Write-Host "请关闭占用该端口的程序后重试。" -ForegroundColor Yellow
    pause
    exit 1
}

try {
    `$tcpListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse(`$apiHost), `$apiPort)
    `$tcpListener.Start()
    `$tcpListener.Stop()
}
catch {
    Write-Host "[错误] 端口 `$apiPort 无法绑定。" -ForegroundColor Red
    Write-Host "可能已有程序占用该端口，请关闭后重试。" -ForegroundColor Yellow
    Write-Host "详细信息: `$(`$_.Exception.Message)" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[信息] Python: `$pythonExe" -ForegroundColor Green
Write-Host "[信息] 地址: http://`$(`$apiHost):`$apiPort" -ForegroundColor Green
Write-Host "[信息] 启动服务..." -ForegroundColor Green
Write-Host ""

# 启动服务
& `$pythonExe `$mainPy
`$exitCode = `$LASTEXITCODE
if (`$exitCode -ne 0) {
    Write-Host ""
    Write-Host "[错误] 服务已退出，退出码: `$exitCode" -ForegroundColor Red
    Write-Host "请检查上方日志中的错误信息。" -ForegroundColor Yellow
}

pause
"@

$startPs1 | Out-File -LiteralPath (Join-Path $OUTPUT_DIR "start.ps1") -Encoding UTF8

# ============================================
# 步骤 5: 创建说明文档
# ============================================

Write-Step "步骤 5: 创建说明文档"

$readme = @"
# UzonCalc API - 便携式版本

## 简介

这是 UzonCalc API 的便携式版本，无需安装 Python 即可运行。

## 系统要求

- Windows 10/11 (64位)
- 至少 200MB 磁盘空间

## 使用方法

### 方法 1: PowerShell 脚本

右键点击 `start.ps1`，选择"使用 PowerShell 运行"。

### 方法 2: 手动启动

```bash
cd /d <解压目录>
dist\python-embedded\python.exe main.py
```

## 访问方式

启动后，在浏览器中访问：

- API 文档: http://127.0.0.1:3345/docs
- 主页: http://127.0.0.1:3345/

## 停止服务

在命令行窗口中按 `Ctrl + C` 即可停止服务。

## 目录结构

```
UzonCalc-Portable/
├── dist/
│   └── python-embedded/ # 嵌入式 Python 环境
├── app/                 # 应用代码
├── config/              # 配置文件
├── data/                # 数据文件
├── main.py              # 主程序入口
├── start.ps1            # PowerShell 启动脚本
└── README.txt           # 本文件
```

## 注意事项

1. 首次运行可能需要几秒钟初始化数据库
2. 确保端口 3345 未被其他程序占用
3. 不要删除或修改 `dist/python-embedded` 目录

## 故障排查

### 端口被占用

如果提示端口被占用，请：
1. 找到占用端口的程序并关闭
2. 或修改配置文件使用其他端口

### Python 未找到

确保 `dist/python-embedded` 目录完整，如有问题请重新解压。

## 技术支持

如遇问题，请访问项目主页或联系技术支持。

---

版本: 1.0.0
日期: $(Get-Date -Format "yyyy-MM-dd")
"@

$readme | Out-File -LiteralPath (Join-Path $OUTPUT_DIR "README.txt") -Encoding UTF8

# ============================================
# 步骤 6: 清理不必要的文件
# ============================================

Write-Step "步骤 6: 清理不必要的文件"

$excludePatterns = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".git",
    ".gitignore",
    "*.log"
)

foreach ($pattern in $excludePatterns) {
    Write-Info "清理: $pattern"
    Get-ChildItem -LiteralPath $OUTPUT_DIR -Filter $pattern -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# ============================================
# 步骤 7: 计算大小
# ============================================

Write-Step "打包完成"

$size = (Get-ChildItem -LiteralPath $OUTPUT_DIR -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Info "输出目录: $OUTPUT_DIR"
Write-Info "总大小: $([Math]::Round($size, 2)) MB"
