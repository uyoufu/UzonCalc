"""
远程 Sandbox 服务端

独立的 FastAPI 应用，用于在容器中运行 sandbox 执行逻辑
可以独立部署，通过 HTTP 接口提供 sandbox 执行服务
"""

from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from core.execution_result import ExecutionResult
from core.executor_local import LocalSandboxExecutor

import logging

logger = logging.getLogger("uzoncalc_sandbox")


# Request/Response 模型
class ExecuteScriptRequest(BaseModel):
    script_path: str
    defaults: Dict[str, Dict[str, Any]] = {}
    is_silent: bool = False
    package_root: str | None = None


class ContinueExecutionRequest(BaseModel):
    execution_id: str
    defaults: Dict[str, Dict[str, Any]]


class TerminateRequest(BaseModel):
    execution_id: str


# 全局执行器实例
executor: LocalSandboxExecutor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global executor
    executor = LocalSandboxExecutor()
    logger.info("Remote Sandbox Server started")
    yield
    logger.info("Remote Sandbox Server shutting down")


# 创建 FastAPI 应用
app = FastAPI(
    title="UzonCalc Remote Sandbox Service",
    description="远程 Sandbox 执行服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/sandbox/execute", response_model=ExecutionResult)
async def execute_script(request: ExecuteScriptRequest) -> ExecutionResult:
    """
    执行脚本
    """
    if executor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Executor not initialized",
        )
    try:
        result = await executor.execute_script(
            script_path=request.script_path,
            defaults=request.defaults,
            is_silent=request.is_silent,
            package_root=request.package_root,
        )
        return result
    except Exception as e:
        logger.exception(f"Error executing script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/sandbox/continue", response_model=ExecutionResult)
async def continue_execution(request: ContinueExecutionRequest) -> ExecutionResult:
    """
    继续执行（提交用户输入）
    """
    if executor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Executor not initialized",
        )
    try:
        result = await executor.continue_execution(
            execution_id=request.execution_id,
            defaults=request.defaults,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error continuing execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/sandbox/terminate")
async def terminate_execution(request: TerminateRequest):
    """
    终止执行
    """
    if executor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Executor not initialized",
        )
    try:
        await executor.terminate(request.execution_id)
        return {"status": "terminated"}
    except Exception as e:
        logger.exception(f"Error terminating execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "sandbox_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )
