# 沙箱执行模块文档

## 概述

该模块负责在隔离的沙箱环境中执行 UzonCalc 计算代码。可以：
- 独立在同一进程中运行（开发模式）
- 部署到 Docker 容器中运行（生产模式）

## 核心组件

### 1. `executor.py` - 沙箱执行器
主执行引擎，负责：
- 加载计算函数（支持动态导入）
- 管理执行生命周期
- 与生成器管理器配合处理 UI 中断和恢复

### 2. `module_loader.py` - 模块加载器
安全的动态加载器：
- 动态导入 `.py` 文件
- 自动检测文件变化（mtime）
- 缓存管理，避免重复加载
- 路径白名单验证

### 3. `generator_manager.py` - 生成器管理
异步生成器生命周期管理：
- 管理多个并发的计算会话
- 处理 UI 中断点
- 恢复执行并注入用户输入
- 会话超时清理

### 4. `client.py` - 沙箱客户端
提供两种通信方式：
- **LocalSandboxClient**: 进程内直接调用（开发/单机）
- **RemoteSandboxClient**: HTTP 远程调用（容器/分布式）

### 5. `rpc.py` - RPC 接口
处理来自外部的请求，支持的操作：
- `execute`: 启动执行
- `resume`: 继续执行
- `cancel`: 取消执行
- `get_session`: 获取会话状态
- `health_check`: 健康检查

## 架构设计

```
┌─────────────────────────────────────────┐
│          前端 (Vue.js)                  │
└──────────────────┬──────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────┐
│       API 服务器 (FastAPI)              │
│  calc_execution.py controller           │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │ 本地模式：直接调用
        │              ┌──────▼─────────┐
        │ RPC (HTTP)   │ 容器模式：远程调用
        │              └──────▲─────────┘
        │                     │
┌───────▼─────────────────────┴──────────┐
│  沙箱执行器 (Sandbox Container)         │
│ ┌─────────────────────────────────────┐ │
│ │  CalcSandboxExecutor                │ │
│ │  - GeneratorManager                 │ │
│ │  - SandboxModuleLoader              │ │
│ │  - 异步生成器生命周期管理            │ │
│ └─────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

## 执行流程

### 第一步：启动执行

```python
# API 层调用
result = await calc_execution_service.start_execution(
    file_path="/path/to/calc.py",
    func_name="sheet",
    session_id="abc123",
    params={"input": 100}
)

# 返回结果示例
{
    "status": "waiting_ui",
    "session_id": "abc123",
    "ui": {
        "title": "输入参数",
        "fields": [
            {
                "name": "value",
                "type": "number",
                "label": "请输入值",
                "default": None,
                "options": None
            }
        ]
    }
}
```

### 第二步：继续执行

```python
# 用户填完表单后
result = await calc_execution_service.resume_execution(
    session_id="abc123",
    user_input={"value": 200}
)

# 如果还有 UI，再次返回，否则返回完整结果
{
    "status": "completed",
    "session_id": "abc123",
    "result": "<html>...计算结果...</html>"
}
```

## 部署模式

### 开发模式（进程内）
```python
from app.sandbox.executor import CalcSandboxExecutor
from app.sandbox.client import LocalSandboxClient, set_sandbox_client

executor = CalcSandboxExecutor(
    safe_dirs=["/path/to/calc/files"]
)
set_sandbox_client(LocalSandboxClient(executor))
```

### 生产模式（容器）

#### 启动沙箱服务（独立容器）
```python
# sandbox_service.py
from app.sandbox.executor import CalcSandboxExecutor
from app.sandbox.rpc import rpc_execute, rpc_resume, rpc_cancel
from fastapi import FastAPI

app = FastAPI()
executor = CalcSandboxExecutor(safe_dirs=["/calc/files"])

@app.on_event("startup")
async def startup():
    await executor.initialize()

@app.on_event("shutdown")
async def shutdown():
    await executor.shutdown()

@app.post("/sandbox/execute")
async def execute_endpoint(request: ExecuteRequest):
    return await rpc_execute(request)

# ... 其他端点
```

#### 配置 API 服务器连接
```python
from app.sandbox.client import RemoteSandboxClient, set_sandbox_client

# 连接到远程沙箱容器
set_sandbox_client(
    RemoteSandboxClient(base_url="http://sandbox-container:3346")
)
```

#### Docker Compose 示例
```yaml
services:
  api:
    image: uzon-calc-api:latest
    ports:
      - "8000:8000"
    depends_on:
      - sandbox
    environment:
      SANDBOX_URL: "http://sandbox:3346"

  sandbox:
    image: uzon-calc-sandbox:latest
    ports:
      - "3346:3346"
    volumes:
      - ./calc-files:/calc/files
    environment:
      SAFE_DIRS: "/calc/files"
```

## API 端点

### POST `/v1/calc/execution/start`
启动计算执行

### POST `/v1/calc/execution/resume`
继续执行（提交 UI 输入）

### POST `/v1/calc/execution/cancel`
取消执行

### GET `/v1/calc/execution/session/{session_id}`
获取会话状态

### GET `/v1/calc/execution/sessions`
获取所有活跃会话

### POST `/v1/calc/execution/invalidate-cache`
使模块缓存失效

## 重要特性

### 1. 异步生成器
- 函数中的 `UI()` 调用被转换为 `yield`
- 暂停执行点自动保留函数栈
- 用户输入通过 `asend()` 注入，继续执行

### 2. 动态加载与热重载
- 支持检测文件修改时间（mtime）
- 自动缓存失效和重新加载
- 前端通过 `invalidate-cache` API 触发手动失效

### 3. 会话管理
- 每个计算对应一个唯一的 session_id
- 自动超时清理（默认 1 小时）
- 支持并发执行多个计算

### 4. 隔离与安全
- 路径白名单机制
- 生成器沙箱执行
- 模块导入隔离

## 配置选项

### CalcSandboxExecutor
```python
executor = CalcSandboxExecutor(
    safe_dirs=["/path/1", "/path/2"],  # 路径白名单
    session_timeout=3600               # 会话超时（秒）
)
```

### GeneratorManager
```python
manager = GeneratorManager(
    cleanup_interval=300  # 清理间隔（秒）
)
```

## 错误处理

所有操作都返回标准的 HTTP 响应：

```json
{
    "status": "error",
    "session_id": "abc123",
    "error": "错误信息"
}
```

常见错误：
- `FileNotFoundError`: 文件不存在
- `ValueError`: 路径不安全、函数不存在
- `ImportError`: 导入失败
- 会话超时或不存在
