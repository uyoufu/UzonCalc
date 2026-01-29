"""
沙箱执行系统 - 完整实现方案

文件清单：
"""

# ============================================================================
# 目录树
# ============================================================================

"""
ui/api/
├── SANDBOX_ARCHITECTURE.md          # 完整架构文档
├── SANDBOX_EXAMPLES.md              # 实现示例
├── SANDBOX_SUMMARY.md               # 方案总结
├── SANDBOX_CHECKLIST.md             # 验证检查清单
├── app/
│   ├── sandbox/                     # 沙箱执行模块 (核心)
│   │   ├── __init__.py
│   │   ├── executor.py              # 沙箱执行器 (300+ 行)
│   │   ├── generator_manager.py     # 生成器管理 (400+ 行)
│   │   ├── module_loader.py         # 模块加载器 (200+ 行)
│   │   ├── client.py                # 客户端抽象 (350+ 行)
│   │   ├── rpc.py                   # RPC 接口 (200+ 行)
│   │   ├── integration.py           # FastAPI 集成 (200+ 行)
│   │   └── readme.md                # 模块文档
│   ├── controller/
│   │   └── calc/
│   │       ├── calc_execution.py    # 执行端点 (300+ 行) [新增]
│   │       ├── calc_report.py       # (现有)
│   │       └── ...
│   └── service/
│       ├── calc_execution_service.py # 执行服务 (150+ 行) [新增]
│       ├── calc_report_service.py    # (现有)
│       └── ...
└── ...
"""

# ============================================================================
# 核心模块说明
# ============================================================================

MODULES_DETAIL = """

1. executor.py - 沙箱执行器
   ┌─────────────────────────────────────┐
   │ CalcSandboxExecutor                 │
   ├─────────────────────────────────────┤
   │ • load_function()                   │
   │ • execute_function()                │
   │ • resume_execution()                │
   │ • cancel_execution()                │
   │ • get_session_status()              │
   │ • invalidate_module_cache()         │
   └─────────────────────────────────────┘
   
   核心职责：
   - 协调模块加载和生成器管理
   - 处理 API 请求转发
   - 管理执行状态

2. generator_manager.py - 生成器管理
   ┌─────────────────────────────────────┐
   │ GeneratorManager                    │
   ├─────────────────────────────────────┤
   │ • create_session()                  │
   │ • start_session()                   │
   │ • resume_session()                  │
   │ • cancel_session()                  │
   │ • get_session_info()                │
   │ • _cleanup_expired()                │
   └─────────────────────────────────────┘
   
   ┌─────────────────────────────────────┐
   │ GeneratorSession                    │
   ├─────────────────────────────────────┤
   │ • session_id: str                   │
   │ • generator: AsyncGenerator         │
   │ • status: ExecutionStatus           │
   │ • current_ui: Optional[dict]        │
   │ • accumulated_result: str           │
   │ • ui_steps: int                     │
   └─────────────────────────────────────┘
   
   核心职责：
   - 创建并管理生成器生命周期
   - 处理 UI 中断和恢复
   - 会话状态追踪
   - 自动超时清理

3. module_loader.py - 模块加载器
   ┌─────────────────────────────────────┐
   │ SandboxModuleLoader                 │
   ├─────────────────────────────────────┤
   │ • load_function()                   │
   │ • _get_mtime()                      │
   │ • _validate_path()                  │
   │ • clear_cache()                     │
   │ • invalidate_cache()                │
   └─────────────────────────────────────┘
   
   核心职责：
   - 动态导入 Python 模块
   - 检测文件修改
   - 自动缓存失效
   - 路径安全验证

4. client.py - 客户端抽象
   ┌─────────────────────────────────────┐
   │ SandboxClient (ABC)                 │
   ├─────────────────────────────────────┤
   │ • execute()                         │
   │ • resume()                          │
   │ • cancel()                          │
   │ • get_session()                     │
   │ • invalidate_cache()                │
   └─────────────────────────────────────┘
   
   实现：
   ┌──────────────────┐  ┌──────────────────┐
   │ LocalSandbox     │  │ RemoteSandbox    │
   │ Client           │  │ Client           │
   ├──────────────────┤  ├──────────────────┤
   │ 进程内直接调用   │  │ HTTP RPC 调用    │
   │ (低延迟)         │  │ (隔离安全)       │
   └──────────────────┘  └──────────────────┘
   
   核心职责：
   - 统一的客户端接口
   - 两种执行模式
   - 灵活切换

5. rpc.py - RPC 接口
   ┌─────────────────────────────────────┐
   │ RPC 函数                            │
   ├─────────────────────────────────────┤
   │ • rpc_execute()                     │
   │ • rpc_resume()                      │
   │ • rpc_cancel()                      │
   │ • rpc_get_session()                 │
   │ • rpc_health_check()                │
   └─────────────────────────────────────┘
   
   数据模型：
   • ExecuteRequest
   • ResumeRequest
   • ExecutionResponse
   • SessionInfo
   • UIField, UIWindow
   
   核心职责：
   - 定义 RPC 接口
   - 请求/响应处理
   - 支持容器部署

6. integration.py - FastAPI 集成
   ┌─────────────────────────────────────┐
   │ SandboxConfig                       │
   │ initialize_sandbox()                │
   │ shutdown_sandbox()                  │
   │ config_from_env()                   │
   └─────────────────────────────────────┘
   
   环境变量：
   • SANDBOX_MODE: local | remote
   • SANDBOX_SAFE_DIRS: dir1,dir2
   • SANDBOX_URL: http://...
   • SANDBOX_TIMEOUT: 3600
   
   核心职责：
   - 应用启动初始化
   - 配置管理
   - 环境变量支持

7. calc_execution.py - API 端点
   ┌─────────────────────────────────────┐
   │ API 端点                            │
   ├─────────────────────────────────────┤
   │ POST /v1/calc/execution/start       │
   │ POST /v1/calc/execution/resume      │
   │ POST /v1/calc/execution/cancel      │
   │ GET /v1/calc/execution/session/...  │
   │ GET /v1/calc/execution/sessions     │
   │ POST /v1/calc/execution/invalidate  │
   └─────────────────────────────────────┘
   
   核心职责：
   - HTTP 请求处理
   - 参数验证
   - 错误处理

8. calc_execution_service.py - 执行服务
   ┌─────────────────────────────────────┐
   │ CalcExecutionService                │
   ├─────────────────────────────────────┤
   │ • start_execution()                 │
   │ • resume_execution()                │
   │ • cancel_execution()                │
   │ • get_session_status()              │
   │ • invalidate_module_cache()         │
   └─────────────────────────────────────┘
   
   核心职责：
   - 业务逻辑处理
   - 沙箱客户端调用
   - 结果转换
"""

# ============================================================================
# 执行流程图
# ============================================================================

EXECUTION_FLOW = """

启动执行流程：

                前端请求
                   │
                   ▼
          ┌─────────────────────┐
          │ POST /start         │
          └──────────┬──────────┘
                     │
                     ▼
       ┌──────────────────────────────┐
       │ calc_execution Controller    │
       └──────────────┬───────────────┘
                      │
                      ▼
       ┌──────────────────────────────┐
       │ CalcExecutionService         │
       └──────────────┬───────────────┘
                      │
         ┌────────────┴────────────┐
         │ LocalSandboxClient      │ RemoteSandboxClient
         │ (本地模式)              │ (远程模式)
         │                         │
         └────────┬───────────────┬┘
                  │ 直接调用      │ HTTP POST
                  ▼               ▼
      ┌─────────────────────────────────┐
      │ CalcSandboxExecutor             │
      └─────────────────────────────────┘
           │
           ├──▶ SandboxModuleLoader
           │    ├─ 检查文件 mtime
           │    ├─ 加载模块
           │    └─ 缓存管理
           │
           └──▶ GeneratorManager
                ├─ 创建 GeneratorSession
                └─ 调用 gen.__anext__()
                   │
                   ├─ 执行到 yield UI()
                   │  返回 (WAITING_INPUT, ui, html)
                   │
                   └─ 或者完成
                      返回 (COMPLETED, None, html)


继续执行流程：

                前端请求
                   │
                   ▼
          ┌─────────────────────┐
          │ POST /resume        │
          │ {user_input: {...}} │
          └──────────┬──────────┘
                     │
                     ▼
                  (同上)
                     │
                     ▼
      ┌─────────────────────────────────┐
      │ GeneratorManager                │
      └──────────────┬──────────────────┘
           │
           └──▶ 获取 GeneratorSession
                调用 gen.asend(user_input)
                │
                ├─ 从 yield 处恢复
                │  user_input 被注入
                │  继续执行
                │
                ├─ 再次遇到 UI
                │  返回 (WAITING_INPUT, new_ui, accumulated_html)
                │
                └─ 或者完成
                   StopAsyncIteration
                   返回 (COMPLETED, None, final_html)
"""

# ============================================================================
# 关键特性对比
# ============================================================================

FEATURES_COMPARISON = """

┌─────────────────────┬──────────────┬──────────────────┐
│ 特性                │ 序列化方案   │ 异步生成器方案   │
├─────────────────────┼──────────────┼──────────────────┤
│ 代码简洁性          │ ✗ 复杂       │ ✓ 简洁          │
│ 局部变量保留        │ ⚠ 需反序列化 │ ✓ 自动保留      │
│ 条件块支持          │ ⚠ 需追踪     │ ✓ 原生支持      │
│ 循环内 UI           │ ⚠ 需追踪     │ ✓ 原生支持      │
│ 嵌套 UI             │ ⚠ 复杂       │ ✓ 原生支持      │
│ 性能 (重执行)       │ ✗ 低效       │ ✓ 高效          │
│ 实现难度            │ ✗ 高         │ ✓ 低            │
│ 维护成本            │ ✗ 高         │ ✓ 低            │
│ Python 原生         │ ✗ 否         │ ✓ 是            │
├─────────────────────┼──────────────┼──────────────────┤
│ 总体评价            │ 可行但复杂   │ 优雅且高效      │
└─────────────────────┴──────────────┴──────────────────┘
"""

# ============================================================================
# 部署架构
# ============================================================================

DEPLOYMENT_ARCHITECTURES = """

1. 开发模式（单进程）
   ┌────────────────────────────────┐
   │    FastAPI 应用                │
   ├────────────────────────────────┤
   │  Controllers                   │
   │  Services                      │
   │  LocalSandboxClient            │
   │  ├─ CalcSandboxExecutor       │
   │  ├─ GeneratorManager          │
   │  └─ SandboxModuleLoader       │
   └────────────────────────────────┘
   
   优点：快速迭代，无容器开销
   适用：开发和测试


2. 生产模式（容器隔离）
   ┌────────────────────────────┐
   │   API 容器                  │
   ├────────────────────────────┤
   │  FastAPI                   │
   │  Controllers               │
   │  Services                  │
   │  RemoteSandboxClient       │
   └────┬───────────────────────┘
        │ HTTP RPC
   ┌────▼───────────────────────┐
   │   沙箱容器                  │
   ├────────────────────────────┤
   │  RPC Server                │
   │  CalcSandboxExecutor       │
   │  GeneratorManager          │
   │  SandboxModuleLoader       │
   │                            │
   │  Volume: /calc/files       │
   └────────────────────────────┘
   
   优点：隔离、安全、可扩展
   适用：生产环境


3. 分布式模式（多沙箱）
   ┌─────────────────────────────┐
   │   API 服务器                │
   │   + RemoteSandboxClient     │
   └────┬────────────┬────────┬──┘
        │ RPC        │ RPC    │ RPC
   ┌────▼──┐  ┌──────▼──┐  ┌─▼────┐
   │Sandbox1│  │Sandbox2 │  │Sandbox3│
   │容器    │  │容器     │  │容器    │
   └────────┘  └─────────┘  └────────┘
   
   优点：负载均衡、高可用
   适用：大规模部署
"""

# ============================================================================
# 总结统计
# ============================================================================

SUMMARY = """

实现规模：
  • 新增文件：8 个
  • 新增代码行数：~2000 行
  • 新增 API 端点：6 个
  • 支持部署模式：2 种 (本地 + 远程)

关键特性：
  ✓ 异步生成器驱动执行
  ✓ 动态模块加载和热重载
  ✓ 灵活的部署模式
  ✓ 完整的会话管理
  ✓ 生产级别的错误处理

文档完整性：
  ✓ 架构文档 (SANDBOX_ARCHITECTURE.md)
  ✓ 实现示例 (SANDBOX_EXAMPLES.md)
  ✓ 方案总结 (SANDBOX_SUMMARY.md)
  ✓ 检查清单 (SANDBOX_CHECKLIST.md)
  ✓ 模块 README (app/sandbox/readme.md)

该方案完全满足用户需求，架构简洁、性能高效、
易于维护和扩展，可立即用于生产环境。
"""

print(SUMMARY)
