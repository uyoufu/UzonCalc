"""
沙箱架构完整方案文档

该文档详细说明了 UzonCalc 异步生成器执行的完整架构设计。
"""

# ============================================================================
# 架构总览
# ============================================================================

"""
┌───────────────────────────────────────────────────────────────────────┐
│                        前端 (Vue.js)                                   │
│                                                                        │
│  ┌────────────────┐     ┌─────────────┐     ┌──────────────┐         │
│  │ CalcReportViewer│────▶│ InputForm   │────▶│ ResultViewer│         │
│  └────────────────┘     └─────────────┘     └──────────────┘         │
│         │                                           ▲                  │
│         │ 1. 发起执行                              │ 7. 展示结果       │
│         │ /v1/calc/execution/start                │                   │
│         │                                           │                  │
│         │ 2/3/4... UI 循环                         │                  │
│         │ /v1/calc/execution/resume                │                  │
│         │                                           │                  │
└─────────┼───────────────────────────────────────────┼────────────────┘
          │                                           │
          │ HTTP                                      │ HTTP
          │                                           │
┌─────────▼───────────────────────────────────────────┼────────────────┐
│              API 服务器 (FastAPI)                   │                │
│                                                     │                │
│  ┌─────────────────────────────────────────────┐   │                │
│  │ calc_execution.py Controller                │   │                │
│  │ - start_calc_execution()                    │   │                │
│  │ - resume_calc_execution()                   │   │                │
│  │ - cancel_calc_execution()                   │   │                │
│  │ - get_execution_status()                    │   │                │
│  └─────────────────────────────────────────────┘   │                │
│           │                                         │                │
│           ▼                                         │                │
│  ┌─────────────────────────────────────────────┐   │                │
│  │ calc_execution_service.py Service Layer     │───┘                │
│  │ - get_execution_service()                   │                    │
│  │ - start_execution()                         │                    │
│  │ - resume_execution()                        │                    │
│  └─────────────────────────────────────────────┘                    │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────────────────────────────────┐                    │
│  │ client.py - SandboxClient (Abstract)        │                    │
│  │                                              │                    │
│  │ 实现：                                       │                    │
│  │ - LocalSandboxClient (进程内)               │                    │
│  │ - RemoteSandboxClient (HTTP RPC)           │                    │
│  └─────────────────────────────────────────────┘                    │
└───────────────┬──────────────────────────────────────────────────────┘
                │
                │ 本地模式：直接调用
                │ 或
                │ RPC (HTTP POST)
                │
┌───────────────▼──────────────────────────────────────────────────────┐
│  沙箱执行环境 (可独立容器运行)                                        │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ CalcSandboxExecutor (executor.py)                             │   │
│  │                                                                │   │
│  │ 职责：                                                         │   │
│  │ 1. 加载计算函数 (module_loader.py)                           │   │
│  │ 2. 管理生成器生命周期 (generator_manager.py)                 │   │
│  │ 3. 处理 UI 中断和恢复                                        │   │
│  │                                                                │   │
│  │ ┌──────────────────────────────────────────────────────────┐ │   │
│  │ │ SandboxModuleLoader                                      │ │   │
│  │ │ - load_function(file_path, func_name)                   │ │   │
│  │ │ - 文件 mtime 检查 (自动重新加载)                        │ │   │
│  │ │ - 缓存管理 (safe_dirs 白名单)                           │ │   │
│  │ └──────────────────────────────────────────────────────────┘ │   │
│  │                                                                │   │
│  │ ┌──────────────────────────────────────────────────────────┐ │   │
│  │ │ GeneratorManager                                         │ │   │
│  │ │ - create_session(session_id, async_generator)           │ │   │
│  │ │ - start_session() : 首次执行                            │ │   │
│  │ │ - resume_session(user_input) : 继续执行                 │ │   │
│  │ │ - 会话超时自动清理                                      │ │   │
│  │ │ - 返回 (status, current_ui, accumulated_html)           │ │   │
│  │ │                                                          │ │   │
│  │ │ GeneratorSession                                         │ │   │
│  │ │ - session_id: str                                        │ │   │
│  │ │ - generator: AsyncGenerator                             │ │   │
│  │ │ - status: ExecutionStatus (IDLE/RUNNING/WAITING_INPUT) │ │   │
│  │ │ - current_ui: Optional[Window]                          │ │   │
│  │ │ - accumulated_result: str (HTML)                        │ │   │
│  │ │ - ui_steps: int (遇到的 UI 数量)                       │ │   │
│  │ └──────────────────────────────────────────────────────────┘ │   │
│  │                                                                │   │
│  │ ┌──────────────────────────────────────────────────────────┐ │   │
│  │ │ RPC 接口 (rpc.py)                                       │ │   │
│  │ │ - rpc_execute(ExecuteRequest)                           │ │   │
│  │ │ - rpc_resume(ResumeRequest)                             │ │   │
│  │ │ - rpc_cancel(session_id)                                │ │   │
│  │ │ - rpc_get_session(session_id)                           │ │   │
│  │ │ - rpc_health_check()                                    │ │   │
│  │ └──────────────────────────────────────────────────────────┘ │   │
│  │                                                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  负责执行的 UzonCalc 代码：                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ @uzon_calc()                                                   │   │
│  │ async def sheet():  # 被转换为异步生成器                       │   │
│  │     x = 10                                                     │   │
│  │                                                                │   │
│  │     if condition:                                             │   │
│  │         data = yield UI(Window(...))  # ← 暂停点            │   │
│  │                     ↑                                          │   │
│  │         ┌───────────┴────────────┬────────────────┐          │   │
│  │         │ 返回给前端显示 UI    │ 用户填表单     │          │   │
│  │         │ 前端提交输入数据    ├────────────────┤          │   │
│  │         │ asend(data) 注入    │ 继续执行        │          │   │
│  │         └───────────┬────────────┘                │          │   │
│  │                     ▼                             │          │   │
│  │         result = process(x + data["value"])       │          │   │
│  │         ...                                        │          │   │
│  │                                                    ▼          │   │
│  │     return final_result  # → yield 完成           │          │   │
│  │ # → 返回给 API，API 返回给前端                    │          │   │
│  │                                                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# 执行流程详解
# ============================================================================

"""
## 第一次执行 (启动)

1. 前端发起请求：
   POST /v1/calc/execution/start
   {
       "file_path": "/calc/files/example.py",
       "func_name": "sheet",
       "session_id": "session_123",
       "params": {"initial_param": 100}
   }

2. API Controller (calc_execution.py):
   - 调用 CalcExecutionService.start_execution()

3. Service 层 (calc_execution_service.py):
   - 获取 SandboxClient
   - 调用 sandbox_client.execute(...)

4. SandboxClient (client.py):
   
   本地模式 (LocalSandboxClient):
   ├─ 直接调用 executor.execute_function()
   
   远程模式 (RemoteSandboxClient):
   └─ HTTP POST /sandbox/execute

5. 沙箱执行器 (executor.py):
   a) 加载函数：
      func = loader.load_function(file_path, func_name)
   
   b) 调用函数获得生成器：
      gen = func(**params)
   
   c) 启动会话：
      status, ui, html = await generator_manager.start_session(session_id, gen)
   
   d) 在 GeneratorManager 中：
      - 创建 GeneratorSession
      - 调用 await gen.__anext__() 首次运行
      
      如果遇到 UI (函数中的 yield UI(...)):
      └─ 返回 (ExecutionStatus.WAITING_INPUT, ui_dict, "")
      
      如果函数完成:
      └─ 返回 (ExecutionStatus.COMPLETED, None, html)

6. API 返回给前端：
   {
       "status": "waiting_ui",
       "session_id": "session_123",
       "ui": {
           "title": "请输入参数",
           "fields": [
               {
                   "name": "value",
                   "type": "number",
                   "label": "输入值",
                   ...
               }
           ]
       }
   }

## UI 交互循环

7. 前端展示 UI 弹窗，用户填表并提交

8. 前端发起继续请求：
   POST /v1/calc/execution/resume
   {
       "session_id": "session_123",
       "user_input": {"value": 200}
   }

9. Service 层:
   - 调用 sandbox_client.resume(session_id, user_input)

10. 沙箱执行器 (executor.py):
    - 调用 generator_manager.resume_session(session_id, user_input)

11. GeneratorManager:
    a) 获取对应的 GeneratorSession
    b) 调用 await session.generator.asend(user_input)
       - 这会让生成器从 yield UI(...) 处恢复执行
       - user_input 作为 yield 的返回值被注入
       - 函数继续执行下一条语句
    
    c) 如果再次遇到 UI:
       └─ 返回 (ExecutionStatus.WAITING_INPUT, new_ui, accumulated_html)
    
    d) 如果函数完成:
       └─ 返回 (ExecutionStatus.COMPLETED, None, final_html)
    
    e) 如果发生错误:
       └─ 返回 (ExecutionStatus.ERROR, None, error_message)

12. API 返回给前端：
    {
        "status": "completed",
        "session_id": "session_123",
        "result": "<html>...计算结果...</html>"
    }

13. 前端展示最终结果，结束
"""

# ============================================================================
# 关键机制
# ============================================================================

"""
### 1. 异步生成器与 yield 机制

UzonCalc 用户代码示例：
```python
@uzon_calc()
async def sheet():
    x = 10
    
    if x > 5:
        # yield UI，暂停执行
        # 用户在前端填表后，通过 asend() 注入数据
        data = yield UI(Window(
            title="输入参数",
            fields=[...]
        ))
        # 继续执行，data 包含用户输入
        result = x + data["value"]
    
    return result
```

执行步骤：
1. 首次 __anext__() 执行到 yield，暂停
2. 返回 UI 给前端
3. 用户提交数据
4. asend(user_data) 让生成器继续
5. data 变量被赋值为 user_data
6. 继续执行剩余代码
7. StopAsyncIteration 表示生成器完成

### 2. 会话管理

每个计算对应一个 session_id：
- session_id 唯一标识一次计算会话
- 在 GeneratorManager 中存储所有活跃的生成器
- 自动超时清理 (默认 1 小时)
- 支持并发执行多个计算

### 3. 文件加载与热重载

SandboxModuleLoader:
- 缓存已加载的模块
- 检测文件 mtime (修改时间)
- mtime 变化时自动重新加载
- 支持路径白名单

当用户更新计算文件后：
1. 前端调用 /v1/calc/execution/invalidate-cache
2. 沙箱清除该文件的缓存
3. 下次执行时重新加载最新代码

### 4. 结果累积

GeneratorSession 中的 accumulated_result:
- 每次 UI 中断时，之前的 HTML 结果被保存
- 恢复执行后继续积累
- 最终返回完整的 HTML 文档

### 5. 错误处理

ExecutionStatus 枚举值：
- IDLE: 初始状态
- RUNNING: 正在执行
- WAITING_INPUT: 等待用户输入
- COMPLETED: 已完成
- ERROR: 执行出错
- CANCELLED: 已取消

所有异常都被捕获并返回 ERROR 状态
"""

# ============================================================================
# 部署架构
# ============================================================================

"""
## 开发环境（单进程）

┌──────────────────┐
│   FastAPI 应用    │
├──────────────────┤
│   API Controller │
│  Execution Service
│  SandboxClient   │
│  (Local)         │
├──────────────────┤
│  CalcSandboxExecutor
│  GeneratorManager
│  SandboxModuleLoader
└──────────────────┘

配置：
```python
from app.sandbox.executor import CalcSandboxExecutor
from app.sandbox.client import LocalSandboxClient, set_sandbox_client

executor = CalcSandboxExecutor(
    safe_dirs=["/path/to/calc/files"]
)
set_sandbox_client(LocalSandboxClient(executor))
```

## 生产环境（容器隔离）

┌──────────────────────────────┐
│      API Server Container     │
├──────────────────────────────┤
│      FastAPI Application     │
│      - Controllers           │
│      - Services              │
│      - RemoteSandboxClient   │
└──────┬───────────────────────┘
       │ HTTP RPC
┌──────▼───────────────────────┐
│    Sandbox Container          │
├──────────────────────────────┤
│  RPC Server (FastAPI)        │
│  CalcSandboxExecutor         │
│  GeneratorManager            │
│  SandboxModuleLoader         │
│                              │
│  Volume: /calc/files         │
└──────────────────────────────┘

docker-compose.yml:
```yaml
version: '3.8'

services:
  api:
    image: uzon-calc-api:latest
    ports:
      - "8000:8000"
    environment:
      SANDBOX_URL: http://sandbox:3346
    depends_on:
      - sandbox

  sandbox:
    image: uzon-calc-sandbox:latest
    ports:
      - "3346:3346"
    volumes:
      - ./calc-files:/calc/files
    environment:
      SAFE_DIRS: /calc/files
```
"""

# ============================================================================
# 扩展性和未来方向
# ============================================================================

"""
1. gRPC 支持
   - 替换 HTTP 为 gRPC，降低延迟
   - 支持流式传输

2. 生成器状态持久化
   - 将生成器快照保存到数据库
   - 支持长期暂停和恢复
   - 支持跨会话保存

3. 分布式执行
   - 多个沙箱容器负载均衡
   - 会话亲和性保证

4. 监控和日志
   - 详细的执行日志
   - 性能监控
   - 分布式追踪

5. 资源限制
   - 内存限制
   - 执行时间限制
   - CPU 限制
"""
