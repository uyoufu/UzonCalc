"""
计算执行 API 控制器

提供 HTTP 端点供前端调用。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service.calc_execution_service import get_execution_service
from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc/execution",
    tags=["calc-execution"],
)


@router.post("/start")
async def start_calc_execution(
    file_path: str,
    func_name: str,
    session_id: str,
    params: Optional[dict] = None,
    load_from_cache: bool = True,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[dict]:
    """
    启动计算执行

    **功能说明:**
    - 加载并执行指定的计算函数
    - 如果函数中有 UI 定义，则暂停执行并返回 UI
    - 如果函数直接完成，则返回完整的 HTML 结果
    - 支持从缓存加载最近一次的用户输入

    **请求参数:**
    - file_path: 计算文件路径 (required)
    - func_name: 函数名称 (required)
    - session_id: 会话 ID，用于跟踪执行 (required)
    - params: 传递给函数的参数字典 (optional)
    - load_from_cache: 是否加载缓存的输入 (optional, default=true)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "status": "waiting_ui|completed|error",
            "session_id": "...",
            "cached": true/false,
            "ui": {
                "title": "UI 标题",
                "fields": [...]
            },
            "result": "<html>...</html>"
        }
    }
    ```

    **错误处理:**
    - 400: 请求参数错误
    - 404: 文件不存在
    - 500: 执行错误
    """
    try:
        service = get_execution_service()
        service.db_session = db_session
        
        result = await service.start_execution(
            user_id=str(tokenPayloads.id),
            file_path=file_path,
            func_name=func_name,
            session_id=session_id,
            params=params or {},
            load_from_cache=load_from_cache,
        )

        logger.info(
            f"Started execution: userId={tokenPayloads.id}, "
            f"file={file_path}, func={func_name}, session={session_id}"
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return ok(data=result)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
async def resume_calc_execution(
    session_id: str,
    user_input: dict,
    file_path: Optional[str] = None,
    func_name: Optional[str] = None,
    step_number: int = 0,
    total_steps: int = 0,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[dict]:
    """
    继续计算执行

    在用户填完 UI 表单后调用此端点，
    将用户输入发送到沙箱，继续执行计算函数。
    同时自动保存用户的输入到数据库。

    **请求参数:**
    - session_id: 会话 ID (required)
    - user_input: 用户在 UI 中的输入 (required)
    - file_path: 计算文件路径 (optional，用于保存历史)
    - func_name: 函数名 (optional，用于保存历史)
    - step_number: 当前步骤号 (optional, default=0)
    - total_steps: 总步骤数 (optional, default=0)

    **返回数据:**
    同 /start 端点，另外增加 "saved" 字段表示是否已保存

    **错误处理:**
    - 404: 会话不存在或已过期
    - 500: 执行错误
    """
    try:
        service = get_execution_service()
        service.db_session = db_session
        
        result = await service.resume_execution(
            user_id=str(tokenPayloads.id),
            session_id=session_id,
            user_input=user_input,
            file_path=file_path,
            func_name=func_name,
            step_number=step_number,
            total_steps=total_steps,
        )

        logger.info(
            f"Resumed execution: userId={tokenPayloads.id}, "
            f"session={session_id}, "
            f"next_status={result.get('status')}"
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return ok(data=result)

    except Exception as e:
        logger.error(f"Error resuming execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_calc_execution(
    session_id: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[dict]:
    """
    取消计算执行

    **请求参数:**
    - session_id: 会话 ID (required)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "status": "cancelled",
            "session_id": "..."
        }
    }
    ```
    """
    try:
        service = get_execution_service()
        result = await service.cancel_execution(session_id)

        logger.info(
            f"Cancelled execution: userId={tokenPayloads.id}, "
            f"session={session_id}"
        )

        return ok(data=result)

    except Exception as e:
        logger.error(f"Error cancelling execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_execution_status(
    session_id: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[dict]:
    """
    获取执行会话状态

    **请求参数:**
    - session_id: 会话 ID (path parameter)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "session_id": "...",
            "status": "waiting_ui",
            "ui_steps": 2,
            "has_error": false,
            "error_message": null
        }
    }
    ```

    **错误处理:**
    - 404: 会话不存在
    """
    try:
        service = get_execution_service()
        result = await service.get_session_status(session_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )

        return ok(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_all_execution_sessions(
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[list]:
    """
    获取所有活跃的执行会话

    用于监控当前系统中正在执行的计算。

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": [
            {
                "session_id": "...",
                "status": "waiting_ui",
                "created_at": "2026-01-29T...",
                "last_activity": "2026-01-29T...",
                "ui_steps": 1,
                "has_error": false
            }
        ]
    }
    ```
    """
    try:
        service = get_execution_service()
        sessions = await service.get_all_sessions()
        return ok(data=sessions)

    except Exception as e:
        logger.error(f"Error getting all sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate-cache")
async def invalidate_module_cache(
    file_path: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[dict]:
    """
    使模块缓存失效

    当用户更新计算文件后调用此端点，
    确保下次执行时重新加载最新代码。

    **请求参数:**
    - file_path: 要失效的文件路径 (required)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "status": "ok",
            "message": "Cache invalidated for ..."
        }
    }
    ```
    """
    try:
        service = get_execution_service()
        result = await service.invalidate_module_cache(file_path)

        logger.info(
            f"Invalidated cache: userId={tokenPayloads.id}, "
            f"file={file_path}"
        )

        return ok(data=result)

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution-history")
async def get_execution_history(
    file_path: str,
    func_name: str,
    limit: int = 20,
    db_session: AsyncSession = Depends(get_session),
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[dict]:
    """
    获取执行历史

    包含所有完成的执行记录和该函数的已发布版本列表。
    可用于显示用户的执行历史和版本管理界面。

    **请求参数:**
    - file_path: 计算文件路径 (required)
    - func_name: 函数名 (required)
    - limit: 返回历史记录的最大数量 (optional, default=20)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "file_path": "...",
            "func_name": "...",
            "last_execution_at": "2026-01-29T...",
            "input_history": [
                {
                    "step_number": 1,
                    "field_values": {...},
                    "timestamp": "..."
                }
            ],
            "published_versions": [
                {
                    "version_name": "v1.0",
                    "version_number": 1,
                    "published_at": "...",
                    "description": "...",
                    "use_count": 5
                }
            ],
            "completion_percentage": 100.0,
            "total_executions": 3
        }
    }
    ```

    **错误处理:**
    - 404: 未找到执行历史
    """
    try:
        service = get_execution_service()
        service.db_session = db_session
        
        history = await service.get_execution_history(
            user_id=str(tokenPayloads.id),
            file_path=file_path,
            func_name=func_name,
            limit=limit,
        )

        if history is None:
            raise HTTPException(
                status_code=404,
                detail=f"No execution history found for {file_path}.{func_name}"
            )

        logger.info(
            f"Retrieved execution history: userId={tokenPayloads.id}, "
            f"file={file_path}, func={func_name}"
        )

        return ok(data=history)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_version(
    file_path: str,
    func_name: str,
    version_name: str,
    description: Optional[str] = None,
    db_session: AsyncSession = Depends(get_session),
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[dict]:
    """
    发布执行版本

    将最近一次完成的执行过程保存为版本快照。
    用户可以稍后直接从此版本恢复完整结果，
    而无需再次经历输入过程。

    **请求参数:**
    - file_path: 计算文件路径 (required)
    - func_name: 函数名 (required)
    - version_name: 版本名称，如 "v1.0", "初版" (required)
    - description: 版本描述 (optional)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "version_id": 1,
            "version_name": "v1.0",
            "version_number": 1,
            "published_at": "2026-01-29T..."
        }
    }
    ```

    **错误处理:**
    - 404: 未找到完成的执行记录
    - 500: 发布失败
    """
    try:
        service = get_execution_service()
        service.db_session = db_session
        
        result = await service.publish_version(
            user_id=str(tokenPayloads.id),
            file_path=file_path,
            func_name=func_name,
            version_name=version_name,
            description=description,
        )

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Failed to publish version. Ensure there's a completed execution."
            )

        logger.info(
            f"Published version: userId={tokenPayloads.id}, "
            f"file={file_path}, func={func_name}, version={version_name}"
        )

        return ok(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/published-versions")
async def get_published_versions(
    file_path: str,
    func_name: str,
    db_session: AsyncSession = Depends(get_session),
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[list]:
    """
    获取已发布的版本列表

    列出用户已发布的所有版本，
    用于版本选择和直接恢复。

    **请求参数:**
    - file_path: 计算文件路径 (required)
    - func_name: 函数名 (required)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": [
            {
                "version_id": 1,
                "version_name": "v1.0",
                "version_number": 1,
                "description": "初始版本",
                "published_at": "2026-01-29T...",
                "use_count": 5,
                "total_steps": 3
            }
        ]
    }
    ```
    """
    try:
        service = get_execution_service()
        service.db_session = db_session
        
        versions = await service.get_published_versions(
            user_id=str(tokenPayloads.id),
            file_path=file_path,
            func_name=func_name,
        )

        logger.info(
            f"Retrieved published versions: userId={tokenPayloads.id}, "
            f"file={file_path}, func={func_name}, count={len(versions)}"
        )

        return ok(data=versions)

    except Exception as e:
        logger.error(f"Error getting published versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore-from-version")
async def restore_from_version(
    version_id: int,
    db_session: AsyncSession = Depends(get_session),
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
) -> ResponseResult[dict]:
    """
    从已发布的版本直接恢复完整结果

    使用此端点可以快速获取已发布版本的完整 HTML 结果，
    无需再次执行整个计算过程。
    
    工作流程：
    1. 用户选择一个已发布的版本
    2. 调用此端点传入 version_id
    3. 立即返回该版本的完整 HTML 结果
    4. 无需经历任何输入步骤

    **请求参数:**
    - version_id: 要恢复的版本 ID (required)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "status": "completed",
            "version_id": 1,
            "version_name": "v1.0",
            "result": "<html>...完整计算结果...</html>",
            "steps": 3,
            "restored_at": "2026-01-29T..."
        }
    }
    ```

    **错误处理:**
    - 404: 版本不存在或不属于当前用户
    - 500: 恢复失败
    """
    try:
        service = get_execution_service()
        service.db_session = db_session
        
        result = await service.restore_from_version(
            user_id=str(tokenPayloads.id),
            version_id=version_id,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Version not found: {version_id}"
            )

        logger.info(
            f"Restored from version: userId={tokenPayloads.id}, "
            f"version={version_id}"
        )

        return ok(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring from version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
