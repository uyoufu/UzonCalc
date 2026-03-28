# UzonCalc Desktop 部署脚本使用说明

## 功能概述

`deploy.py` 是一个自动化部署脚本，用于打包 UzonCalc Desktop 应用到不同平台（Windows、macOS、Linux）。

## 部署步骤

脚本会自动执行以下操作：

1. **创建发布目录**: 在 `publish/<platform>` 下创建平台特定的发布目录
2. **复制应用文件**: 将 `ui/desktop` 的所有必要文件复制到发布目录
3. **安装 Python 环境**:
   - Windows: 下载并配置 Python Embedded 版本
   - macOS/Linux: 使用系统 Python
4. **复制项目依赖**: 复制 `uzoncalc` 和 `ui/api` 到发布目录
5. **安装 Python 依赖**: 安装所有 requirements.txt 中的依赖包
6. **创建启动脚本**: 
   - Windows: `start.bat`
   - macOS/Linux: `start.sh`
7. **构建 Web 前端**: 执行 `npm run build` 并复制到 `api/data/www`

## 使用方法

### 快捷方式（推荐）

我们提供了平台专用的快捷脚本：

**Windows:**
```cmd
# 完整部署（包含 Web 构建）
deploy_windows.bat

# 快速部署（跳过 Web 构建，适合开发调试）
deploy_windows_quick.bat
```

**macOS:**
```bash
chmod +x deploy_macos.sh
./deploy_macos.sh
```

**Linux:**
```bash
chmod +x deploy_linux.sh
./deploy_linux.sh
```

### 基本用法

```bash
# Windows 平台
python deploy.py --platform windows

# macOS 平台
python deploy.py --platform macos

# Linux 平台
python deploy.py --platform linux
```

### 高级选项

```bash
# 指定 Python 版本（仅 Windows）
python deploy.py --platform windows --python-version 3.12

# 跳过 Web 前端构建（开发调试时）
python deploy.py --platform windows --skip-web-build
```

## 参数说明

- `--platform`: **(必需)** 目标平台，可选值: `windows`, `macos`, `linux`
- `--python-version`: Python Embedded 版本（仅 Windows），可选值: `3.11`, `3.12`，默认: `3.11`
- `--skip-web-build`: 跳过 Web 前端构建步骤

## 前置要求

### 所有平台

- Python 3.7+
- Node.js 和 npm（用于构建 Web 前端）

### Windows

- 网络连接（用于下载 Python Embedded）

### macOS/Linux

- 系统已安装 Python 3
- 系统已安装 pip

## 输出结构

部署完成后，发布目录结构如下：

```
publish/
└── windows/  (或 macos/linux)
    ├── python/           # Python 运行环境（仅 Windows）
    ├── desktop/          # Desktop 应用文件
    │   ├── app.py
    │   ├── service_manager.py
    │   └── requirements.txt
    ├── uzoncalc/         # UzonCalc 核心库
    ├── api/              # API 服务
    │   ├── data/
    │   │   ├── calcs/    # 计算结果目录（空）
    │   │   ├── db/       # 数据库目录（空）
    │   │   └── www/      # Web 前端文件
    │   └── logs/         # 日志目录（空）
    ├── version.json      # 版本信息
    └── start.bat/sh      # 启动脚本
```

### 版本信息

部署完成后会自动生成 `version.json` 文件，包含以下信息：

```json
{
  "version": "1.0.0",
  "platform": "windows",
  "build_time": "2026-02-18T08:45:30.123456",
  "git": {
    "branch": "master",
    "commit": "abc123def456...",
    "short_commit": "abc123d",
    "commit_time": "2026-02-18 08:30:00 +0800"
  }
}
```

## 运行应用

部署完成后，进入发布目录运行启动脚本：

### Windows

```cmd
cd publish\windows
start.bat
```

### macOS/Linux

```bash
cd publish/macos  # 或 publish/linux
./start.sh
```

## 常见问题

### 1. 下载 Python Embedded 失败

- 检查网络连接
- 尝试使用代理或 VPN
- 手动下载后放置到对应位置

### 2. npm build 失败

- 确保已安装 Node.js 和 npm
- 在 `ui/web` 目录执行 `npm install` 安装依赖
- 检查 Node.js 版本是否符合要求

### 3. 依赖安装失败

- 检查 Python 版本
- 尝试升级 pip: `python -m pip install --upgrade pip`
- 检查网络连接，某些包可能需要从 PyPI 下载

### 4. macOS/Linux 平台权限问题

```bash
# 给启动脚本添加执行权限
chmod +x publish/macos/start.sh
```

## 开发调试

在开发过程中，如果只修改了 Python 代码，可以跳过 Web 前端构建：

```bash
python deploy.py --platform windows --skip-web-build
```

这将大大加快部署速度。

### 清理发布目录

使用 `clean.py` 脚本清理发布目录：

```bash
# 清理特定平台
python clean.py --platform windows

# 清理所有平台
python clean.py --platform all
```

## 注意事项

1. 部署前确保所有代码已提交或保存
2. 首次部署可能需要较长时间（下载 Python、安装依赖等）
3. 发布目录会被自动清空重建，注意备份重要数据
4. Windows 平台的 Python Embedded 不包含 tkinter 等某些标准库

## 技术支持

如有问题，请查看日志输出或提交 Issue。
