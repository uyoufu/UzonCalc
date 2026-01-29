"""
沙箱 RPC 服务

通过 HTTP/gRPC 与外部通信的接口。
可以部署在独立容器中。

协议：
- 启动执行：POST /sandbox/execute
- 继续执行：POST /sandbox/resume
- 取消执行：POST /sandbox/cancel
- 查询状态：GET /sandbox/session/{session_id}
"""

import logging
from typing import Optional, Any
from pydantic import BaseModel

from .executor import get_executor

logger = logging.getLogger(__name__)


# ============ 请求/响应数据模型 ============


class ExecuteRequest(BaseModel):
    """执行请求"""

    file_path: str
    func_name: str
    session_id: str
    params: dict[str, Any] = {}


class ResumeRequest(BaseModel):
    """继续执行请求"""

    session_id: str
    user_input: dict[str, Any]


class UIField(BaseModel):
    """UI 字段定义"""

    name: str
    type: str  # "text", "number", "checkbox", "select", etc.
    label: str
    default: Optional[Any] = None
    options: Optional[list[str]] = None


class UIWindow(BaseModel):
    """UI 窗口"""

    title: str
    fields: list[UIField]


class ExecutionResponse(BaseModel):
    """执行响应"""

    status: str  # "waiting_ui", "completed", "error"
    session_id: str
    ui: Optional[UIWindow] = None
    result: Optional[str] = None  # HTML 结果
    error: Optional[str] = None


class SessionInfo(BaseModel):
    """会话信息"""

    session_id: str
    status: str
    ui_steps: int
    has_error: bool
    error_message: Optional[str] = None


# ============ RPC 处理函数 ============


async def rpc_execute(request: ExecuteRequest) -> ExecutionResponse:
    """
    执行计算函数

    返回：
    - status="waiting_ui": 需要用户输入 UI
    - status="completed": 计算完成
    - status="error": 出错
    """
    executor = get_executor()

    try:
        status, ui, html = await executor.execute_function(
            file_path=request.file_path,
            func_name=request.func_name,
            session_id=request.session_id,
            params=request.params,
        )

        if ui:
            return ExecutionResponse(
                status="waiting_ui",
                session_id=request.session_id,
                ui=UIWindow(
                    title=ui["title"],
                    fields=[UIField(**f) for f in ui["fields"]],
                ),
            )
        else:
            return ExecutionResponse(
                status="completed",
                session_id=request.session_id,
                result=html,
            )

    except Exception as e:
        logger.error(f"RPC execute error: {e}", exc_info=True)
        return ExecutionResponse(
            status="error",
            session_id=request.session_id,
            error=str(e),
        )


async def rpc_resume(request: ResumeRequest) -> ExecutionResponse:
    """
    继续执行（用户提交 UI 输入后）
    """
    executor = get_executor()

    try:
        status, ui, html = await executor.resume_execution(
            session_id=request.session_id,
            user_input=request.user_input,
        )

        if ui:
            return ExecutionResponse(
                status="waiting_ui",
                session_id=request.session_id,
                ui=UIWindow(
                    title=ui["title"],
                    fields=[UIField(**f) for f in ui["fields"]],
                ),
            )
        else:
            return ExecutionResponse(
                status="completed",
                session_id=request.session_id,
                result=html,
            )

    except Exception as e:
        logger.error(f"RPC resume error: {e}", exc_info=True)
        return ExecutionResponse(
            status="error",
            session_id=request.session_id,
            error=str(e),
        )


async def rpc_cancel(session_id: str) -> dict:
    """
    取消执行
    """
    executor = get_executor()
    executor.cancel_execution(session_id)
    return {"status": "cancelled", "session_id": session_id}


async def rpc_get_session(session_id: str) -> Optional[SessionInfo]:
    """
    获取会话状态
    """
    executor = get_executor()
    info = executor.get_session_status(session_id)
    if info:
        return SessionInfo(**info)
    return None


async def rpc_get_sessions() -> list[SessionInfo]:
    """
    获取所有活跃会话
    """
    executor = get_executor()
    sessions = executor.get_all_sessions()
    return [SessionInfo(**s) for s in sessions]


async def rpc_invalidate_cache(file_path: str) -> dict:
    """
    使模块缓存失效（文件更新时调用）
    """
    executor = get_executor()
    executor.invalidate_module_cache(file_path)
    return {
        "status": "ok",
        "message": f"Cache invalidated for {file_path}",
    }


async def rpc_get_cache_info() -> dict:
    """
    获取缓存信息
    """
    executor = get_executor()
    return executor.get_cache_info()


async def rpc_health_check() -> dict:
    """
    健康检查
    """
    executor = get_executor()
    sessions = executor.get_all_sessions()
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "cache_info": executor.get_cache_info(),
    }
