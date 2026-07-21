from __future__ import annotations

import argparse
import fnmatch
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DIST_DIR = PROJECT_ROOT / "dist"
EMBEDDED_PYTHON_RELATIVE_DIR = Path("dist/python-embedded")
EMBEDDED_PYTHON_SOURCE_DIR = PROJECT_ROOT / EMBEDDED_PYTHON_RELATIVE_DIR


class BuildError(RuntimeError):
    pass


def write_info(message: str) -> None:
    print(f"[INFO] {message}")


def write_step(message: str) -> None:
    print()
    print("========================================")
    print(message)
    print("========================================")
    print()


def resolve_full_path(path: Path) -> Path:
    return path.resolve()


def assert_path_is_inside(path: Path, parent_path: Path, description: str) -> None:
    full_path = resolve_full_path(path)
    full_parent_path = resolve_full_path(parent_path)
    try:
        full_path.relative_to(full_parent_path)
    except ValueError as exc:
        raise BuildError(f"{description} must be inside {full_parent_path}: {full_path}") from exc
    if full_path == full_parent_path:
        raise BuildError(f"{description} must be inside {full_parent_path}: {full_path}")


def assert_paths_are_separate(first_path: Path, second_path: Path, description: str) -> None:
    first = resolve_full_path(first_path)
    second = resolve_full_path(second_path)
    try:
        first.relative_to(second)
        overlaps = True
    except ValueError:
        try:
            second.relative_to(first)
            overlaps = True
        except ValueError:
            overlaps = False
    if overlaps:
        raise BuildError(f"{description} cannot contain each other: {first} <-> {second}")


def test_invalid_output_name(name: str) -> bool:
    invalid_chars = set('<>:"/\\|?*')
    return (
        not name.strip()
        or Path(name).is_absolute()
        or any(char in invalid_chars for char in name)
        or "/" in name
        or "\\" in name
        or name in {".", ".."}
    )


def run_command(command: list[str], *, cwd: Path, failure_message: str) -> None:
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise BuildError(f"{failure_message}, exit code: {completed.returncode}")


def copy_item(source_path: Path, output_dir: Path) -> None:
    if source_path.is_dir():
        target = output_dir / source_path.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source_path, target)
    else:
        shutil.copy2(source_path, output_dir)


def write_start_script(output_dir: Path) -> None:
    start_script = r'''# UzonCalc API 后台服务启动脚本
$ErrorActionPreference = "Stop"

$apiHost = "127.0.0.1"
$apiPort = 3345

Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UzonCalc API 后台服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonExe = Join-Path $PSScriptRoot "dist\python-embedded\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "[错误] 未找到 Python: $pythonExe" -ForegroundColor Red
    pause
    exit 1
}

$mainPy = Join-Path $PSScriptRoot "main.py"
if (-not (Test-Path $mainPy)) {
    Write-Host "[错误] 未找到入口文件: $mainPy" -ForegroundColor Red
    pause
    exit 1
}

$logDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$logPath = Join-Path $logDir "uzoncalc.log"
try {
    $logStream = [System.IO.File]::Open($logPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $logStream.Close()
}
catch {
    Write-Host "[错误] 日志文件不可写: $logPath" -ForegroundColor Red
    Write-Host "可能已有残留 Python 服务正在占用日志文件，请先关闭后重试。" -ForegroundColor Yellow
    Write-Host "详细信息: $($_.Exception.Message)" -ForegroundColor Yellow
    pause
    exit 1
}

$listenerPid = $null
if (Get-Command -Name Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    $listener = Get-NetTCPConnection -LocalPort $apiPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        $listenerPid = $listener.OwningProcess
    }
}

if (-not $listenerPid) {
    $netstatPattern = "^\s*TCP\s+\S+:$apiPort\s+\S+\s+LISTENING\s+(\d+)\s*$"
    $netstatLine = netstat -ano | Select-String -Pattern $netstatPattern | Select-Object -First 1
    if ($netstatLine -and $netstatLine.Line -match $netstatPattern) {
        $listenerPid = $matches[1]
    }
}

if ($listenerPid) {
    Write-Host "[错误] 端口 $apiPort 已被占用，PID: $listenerPid" -ForegroundColor Red
    Write-Host "请关闭占用该端口的程序后重试。" -ForegroundColor Yellow
    pause
    exit 1
}

try {
    $tcpListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($apiHost), $apiPort)
    $tcpListener.Start()
    $tcpListener.Stop()
}
catch {
    Write-Host "[错误] 端口 $apiPort 无法绑定。" -ForegroundColor Red
    Write-Host "可能已有程序占用该端口，请关闭后重试。" -ForegroundColor Yellow
    Write-Host "详细信息: $($_.Exception.Message)" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[信息] Python: $pythonExe" -ForegroundColor Green
Write-Host "[信息] 地址: http://$($apiHost):$apiPort" -ForegroundColor Green
Write-Host "[信息] 启动服务..." -ForegroundColor Green
Write-Host ""

& $pythonExe $mainPy
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[错误] 服务已退出，退出码: $exitCode" -ForegroundColor Red
    Write-Host "请检查上方日志中的错误信息。" -ForegroundColor Yellow
}

pause
'''
    (output_dir / "start.ps1").write_text(start_script, encoding="utf-8")


def write_readme(output_dir: Path) -> None:
    readme = f"""# UzonCalc API - 便携式版本

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
dist\\python-embedded\\python.exe main.py
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
日期: {date.today().isoformat()}
"""
    (output_dir / "README.txt").write_text(readme, encoding="utf-8")


def cleanup_output(output_dir: Path) -> None:
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        ".git",
        ".gitignore",
        "*.log",
    ]
    for pattern in exclude_patterns:
        write_info(f"Clean: {pattern}")
        for path in sorted(output_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if fnmatch.fnmatch(path.name, pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)


def directory_size_mb(directory: Path) -> float:
    total_size = sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())
    return total_size / 1024 / 1024


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the UzonCalc API portable package.")
    parser.add_argument("--output-name", default="UzonCalc-Portable")
    parser.add_argument("--python-version", default="3.13.14")
    parser.add_argument("--python-cache-root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if test_invalid_output_name(args.output_name):
        raise BuildError(f"OutputName must be a single directory name under dist: {args.output_name}")

    output_dir = (DIST_DIR / args.output_name).resolve()
    embedded_python_output_dir = output_dir / EMBEDDED_PYTHON_RELATIVE_DIR
    assert_path_is_inside(output_dir, DIST_DIR, "Output directory")
    assert_paths_are_separate(output_dir, EMBEDDED_PYTHON_SOURCE_DIR, "Output directory and embedded Python source directory")

    write_step("Step 1: Setup embedded Python")
    setup_script = SCRIPT_DIR / "setup-embedded-python.py"
    if not setup_script.exists():
        raise BuildError(f"setup-embedded-python.py was not found: {setup_script}")

    setup_args = [
        sys.executable,
        str(setup_script),
        "--python-version",
        args.python_version,
        "--target-dir",
        str(EMBEDDED_PYTHON_RELATIVE_DIR),
    ]
    if args.python_cache_root and args.python_cache_root.strip():
        setup_args.extend(["--cache-root", args.python_cache_root])
    run_command(setup_args, cwd=PROJECT_ROOT, failure_message="Embedded Python setup failed")

    write_step("Step 2: Create output directory")
    if output_dir.exists():
        write_info("Cleaning old output directory...")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_info(f"Output directory: {output_dir}")

    write_step("Step 3: Copy project files")
    items_to_copy = ["app", "config", "utils", "main.py", "requirements.txt"]
    for item in items_to_copy:
        source_path = PROJECT_ROOT / item
        if source_path.exists():
            write_info(f"Copy: {item}")
            copy_item(source_path, output_dir)
        else:
            print(f"  Skip missing item: {item}")

    if EMBEDDED_PYTHON_SOURCE_DIR.exists():
        embedded_python_output_dir.parent.mkdir(parents=True, exist_ok=True)
        write_info(f"Copy: {EMBEDDED_PYTHON_RELATIVE_DIR}")
        if embedded_python_output_dir.exists():
            shutil.rmtree(embedded_python_output_dir)
        shutil.copytree(EMBEDDED_PYTHON_SOURCE_DIR, embedded_python_output_dir)
    else:
        print(f"  Skip missing item: {EMBEDDED_PYTHON_RELATIVE_DIR}")

    portable_config_dir = output_dir / "config"
    if portable_config_dir.exists():
        write_info("Set portable runtime environment: prod")
        (portable_config_dir / ".env").write_text("prod", encoding="utf-8")
        portable_dev_config = portable_config_dir / "app.dev.ini"
        if portable_dev_config.exists():
            write_info("Remove development config: config/app.dev.ini")
            portable_dev_config.unlink()
    else:
        print("  Skip missing item: config")

    for data_dir in ["data/db", "data/public", "data/www", "data/calcs"]:
        (output_dir / data_dir).mkdir(parents=True, exist_ok=True)

    write_step("Step 4: Create startup script")
    write_start_script(output_dir)

    write_step("Step 5: Create README")
    write_readme(output_dir)

    write_step("Step 6: Clean unnecessary files")
    cleanup_output(output_dir)

    write_step("Package complete")
    write_info(f"Output directory: {output_dir}")
    write_info(f"Total size: {directory_size_mb(output_dir):.2f} MB")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        print("[WARN] Build cancelled.")
        raise SystemExit(130)
    except BuildError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
