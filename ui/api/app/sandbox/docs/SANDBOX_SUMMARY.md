"""
沙箱执行系统 - 完整实现方案总结
"""

# ============================================================================
# 核心架构
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────┐
│  前端请求                                                           │
│  /v1/calc/execution/start  →  启动执行                             │
│  /v1/calc/execution/resume →  继续执行 (用户提交 UI)              │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  API 层 (FastAPI)                                                   │
│  - calc_execution.py (controller)                                   │
│  - calc_execution_service.py (service)                              │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  沙箱客户端抽象层                                                    │
│  - SandboxClient (interface)                                        │
│  - LocalSandboxClient (进程内)                                      │
│  - RemoteSandboxClient (HTTP RPC)                                   │
└────────────────┬────────────────────────────────────────────────────┘
                 │
        ┌────────┴─────────┐
        │ 本地模式          │ 远程模式
        │ (开发)            │ (容器)
        │                   │
        ▼                   ▼
┌──────────────────┐  ┌────────────────┐
│ 同进程执行        │  │  HTTP RPC      │
│ (低延迟)          │  │ (隔离安全)      │
└──────────────────┘  └────────┬───────┘
        │                      │
        └──────────┬───────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  沙箱执行引擎 (可部署在容器中)                                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ CalcSandboxExecutor                                         │   │
│  │ ├─ SandboxModuleLoader: 动态加载模块 (文件 mtime 检查)     │   │
│  │ └─ GeneratorManager: 异步生成器生命周期管理                │   │
│  │                                                             │   │
│  │    GeneratorSession                                         │   │
│  │    ├─ generator: AsyncGenerator 实例                       │   │
│  │    ├─ status: 执行状态 (IDLE/RUNNING/WAITING_INPUT/...)   │   │
│  │    ├─ current_ui: 当前等待的 UI 窗口                       │   │
│  │    ├─ accumulated_result: 积累的 HTML 结果                 │   │
│  │    └─ ui_steps: 遇到的 UI 数量                             │   │
│  │                                                             │   │
│  │    异步生成器执行:                                          │   │
│  │    1. 首次 __anext__() 执行到 yield UI(...)               │   │
│  │    2. 返回 UI 给前端                                        │   │
│  │    3. 用户提交表单                                          │   │
│  │    4. asend(user_data) 恢复执行                            │   │
│  │    5. yield 返回 user_data，继续执行                        │   │
│  │    6. 如果再有 UI，重复 1-5                               │   │
│  │    7. StopAsyncIteration 表示完成                          │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  RPC 接口 (rpc.py)                                                 │
│  - rpc_execute: 启动执行                                           │
│  - rpc_resume: 继续执行                                            │
│  - rpc_cancel: 取消执行                                            │
│  - rpc_get_session: 获取会话状态                                   │
│  - rpc_health_check: 健康检查                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# 关键特性
# ============================================================================

"""
1. 异步生成器驱动执行
   ✓ 函数在 yield UI(...) 处自然暂停
   ✓ 函数栈自动保留所有局部变量
   ✓ 无需复杂的状态序列化和恢复
   ✓ 原生支持条件、循环、嵌套 UI

2. 动态模块加载
   ✓ 支持文件路径白名单
   ✓ 自动检测文件修改 (mtime)
   ✓ 缓存管理，避免重复加载
   ✓ 文件变化时自动重新加载

3. 灵活的部署模式
   ✓ 本地模式: 开发快速迭代
   ✓ 远程模式: 生产隔离执行
   ✓ 支持 Docker 容器部署
   ✓ 轻松切换，无需代码改动

4. 会话管理
   ✓ 唯一 session_id 标识每次计算
   ✓ 支持并发执行多个计算
   ✓ 自动超时清理 (可配置)
   ✓ 详细的会话信息查询

5. 错误处理
   ✓ 统一的错误响应格式
   ✓ 详细的错误信息
   ✓ 异常自动捕获和记录
   ✓ 优雅的降级处理

6. 扩展性
   ✓ 基于接口的客户端设计
   ✓ 轻松添加新的通信方式 (gRPC 等)
   ✓ 模块化架构，易于维护
   ✓ 支持分布式和微服务部署
"""

# ============================================================================
# 文件结构
# ============================================================================

"""
ui/api/app/sandbox/
├── __init__.py                    # 模块入口
├── executor.py                    # 沙箱执行器 (核心引擎)
├── generator_manager.py           # 生成器生命周期管理
├── module_loader.py               # 动态模块加载器
├── client.py                      # 沙箱客户端 (本地/远程)
├── rpc.py                         # RPC 接口定义
├── integration.py                 # FastAPI 集成
└── readme.md                      # 模块文档

ui/api/app/controller/calc/
├── calc_execution.py              # API 端点 (新增)
├── calc_report.py                 # (现有)
└── ...

ui/api/app/service/
├── calc_execution_service.py      # 执行服务 (新增)
├── calc_report_service.py         # (现有)
└── ...

ui/api/
├── SANDBOX_ARCHITECTURE.md        # 完整架构文档
└── SANDBOX_EXAMPLES.md            # 实现示例
"""

# ============================================================================
# 快速开始
# ============================================================================

"""
1. 本地开发模式

# main.py
from fastapi import FastAPI
from app.sandbox.integration import initialize_sandbox, shutdown_sandbox, SandboxConfig

app = FastAPI()

@app.on_event("startup")
async def startup():
    config = SandboxConfig(
        mode="local",
        safe_dirs=["/path/to/calc/files"],
    )
    await initialize_sandbox(config)

@app.on_event("shutdown")
async def shutdown():
    await shutdown_sandbox()

# 启动应用
uvicorn main:app --reload


2. 远程容器模式

# 编写 docker-compose.yml
version: '3.8'
services:
  api:
    image: uzon-calc-api
    environment:
      SANDBOX_MODE: remote
      SANDBOX_URL: http://sandbox:3346
    depends_on:
      - sandbox
  
  sandbox:
    image: uzon-calc-sandbox
    ports:
      - "3346:3346"
    volumes:
      - ./calc-files:/calc/files

# 启动
docker-compose up


3. 环境变量配置

# 本地模式
export SANDBOX_MODE=local
export SANDBOX_SAFE_DIRS=/path/to/calc1,/path/to/calc2
export SANDBOX_TIMEOUT=3600

# 远程模式
export SANDBOX_MODE=remote
export SANDBOX_URL=http://sandbox-container:3346
export SANDBOX_TIMEOUT=7200
"""

# ============================================================================
# 工作流程示例
# ============================================================================

"""
前端请求流程：

1. 用户在前端输入计算文件和初始参数
   
   POST /v1/calc/execution/start
   {
       "file_path": "/calc/files/beam.py",
       "func_name": "sheet",
       "session_id": "session_abc123",
       "params": {"initial_length": 10}
   }

2. API 转发给 Service，Service 调用沙箱

3. 沙箱加载函数并执行：
   
   func = loader.load_function(
       "/calc/files/beam.py",  # 检查文件 mtime
       "sheet"
   )
   gen = func(initial_length=10)  # 调用函数
   
   await generator_manager.start_session(
       "session_abc123",
       gen
   )

4. 生成器执行到第一个 yield UI(...)，暂停

5. API 返回给前端：
   
   {
       "status": "waiting_ui",
       "session_id": "session_abc123",
       "ui": {
           "title": "输入梁的参数",
           "fields": [...]
       }
   }

6. 前端展示 UI，用户填表并提交

7. 前端发送用户输入：
   
   POST /v1/calc/execution/resume
   {
       "session_id": "session_abc123",
       "user_input": {"beam_width": 0.5, "beam_height": 0.8}
   }

8. 沙箱恢复生成器执行：
   
   result = await generator.asend({
       "beam_width": 0.5,
       "beam_height": 0.8
   })
   
   generator 从 yield 处恢复，
   user_input 作为 yield 的返回值被注入

9. 函数继续执行，积累 HTML 结果

10. 如果再有 UI，重复步骤 4-8
    如果完成，返回最终结果给前端

11. 前端展示计算报告 HTML 结果
"""

# ============================================================================
# 核心优势
# ============================================================================

"""
1. 架构简洁
   ✓ 利用异步生成器的自然特性
   ✓ 无需复杂的状态机
   ✓ 代码易理解，易维护

2. 执行高效
   ✓ 暂停点恢复，无重复执行
   ✓ 局部变量自然保留
   ✓ 支持长链 UI 交互

3. 隔离安全
   ✓ 容器部署提高安全性
   ✓ 路径白名单防止任意执行
   ✓ RPC 接口隔离执行环境

4. 扩展灵活
   ✓ 客户端接口抽象
   ✓ 轻松支持新的通信协议
   ✓ 支持分布式和负载均衡

5. 开发高效
   ✓ 本地和远程模式无缝切换
   ✓ 环境变量配置
   ✓ 完整的文档和示例
"""

# ============================================================================
# 扩展方向
# ============================================================================

"""
1. gRPC 支持
   - 替换 HTTP，降低延迟
   - 支持双向流式传输

2. 生成器快照
   - 保存执行状态到数据库
   - 支持长期暂停和跨会话恢复

3. 分布式执行
   - 多个沙箱容器负载均衡
   - 会话亲和性保证

4. 资源限制
   - 内存限制 (Docker limits)
   - 执行时间限制 (timeout)
   - CPU 限制 (Docker limits)

5. 监控和日志
   - 执行详细日志
   - 性能监控
   - 分布式追踪 (Jaeger)

6. 错误恢复
   - 异常重试机制
   - 熔断器模式
   - 降级策略
"""

# ============================================================================
# 总结
# ============================================================================

"""
该方案使用异步生成器作为核心机制，实现了一个简洁而强大的
计算执行系统。通过沙箱隔离、模块动态加载、会话管理等功能，
支持 UzonCalc 中的条件 UI 交互、文件热重载和容器部署。

关键亮点：
- 异步生成器 yield 机制完美适配 UI 中断
- 函数栈自动保留，无需复杂的状态序列化
- 本地和远程模式无缝切换
- 生产级别的隔离和安全设计
- 模块化架构，易于扩展

该系统可立即用于生产环境，同时保留了充足的扩展空间。
"""
