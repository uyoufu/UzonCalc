import os
import asyncio
from dataclasses import asdict
from typing import Optional, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_archive import CalcReportArchive
from app.sandbox.core.execution_result import ExecutionResult
from app.sandbox.core.executor_interface import ISandboxExecutor
from app.sandbox.core.executor_local import LocalSandboxExecutor
from app.sandbox.core.executor_remote import RemoteSandboxExecutor
from config import logger, app_config
from uzoncalc.utils_core.dot_dict import deep_update


_executor_instance: ISandboxExecutor | None = None


def get_sandbox_executor() -> ISandboxExecutor:
    """
    获取 sandbox 执行器单例

    根据配置返回本地或远程执行器
    """
    global _executor_instance

    if _executor_instance is not None:
        return _executor_instance

    mode = app_config.sandbox_mode

    if mode == "local":
        logger.info("Using local sandbox executor (in-process)")
        _executor_instance = LocalSandboxExecutor()
    elif mode == "remote":
        remote_url = app_config.sandbox_remote_url
        remote_timeout = app_config.sandbox_remote_timeout
        logger.info(
            f"Using remote sandbox executor: {remote_url} (timeout: {remote_timeout}s)"
        )
        _executor_instance = RemoteSandboxExecutor(
            base_url=remote_url,
            timeout=remote_timeout,
        )
    else:
        raise ValueError(f"Unknown sandbox mode: {mode}. Expected 'local' or 'remote'")

    return _executor_instance


def _get_report_file_path(user_id: int, report_name: str):
    package_root = os.path.abspath(f"data/calcs/{user_id}")

    # report_name 可能是绝对路径
    if os.path.isabs(report_name):
        return (report_name, package_root)

    possible_path = f"{package_root}/{report_name.replace('.py','')}.py"
    # 判断文件是否存在
    if not os.path.isfile(possible_path):
        raise FileNotFoundError(f"CalcReport script file not found: {possible_path}")

    return (possible_path, package_root)


async def start_execution(
    db_session: AsyncSession,
    user_id: int,
    reportId: int,
    defaults: dict[str, dict[str, Any]] = {},
    is_silent: bool = False,
) -> ExecutionResult:
    """
    启动计算执行
    :return: 字典，包含 execution_id 等信息
    返回值示例：
    {
        "execution_id": "some-unique-id",
        "window":{},
        "resultUrl": "public/path/to/result"
    }
    """

    logger.info(f"Starting execution: user={user_id}, reportId={reportId}")

    # 根据 id 获取 CalcReport
    calc_report = await db_session.scalar(
        select(CalcReport).where(CalcReport.id == reportId)
    )
    if not calc_report:
        raise ValueError(f"CalcReport with id {reportId} not found")

    # 计算脚本路径
    (file_path, package_root) = _get_report_file_path(user_id, calc_report.name)

    # 读取一次的历史输入
    last_archive = await db_session.scalar(
        select(CalcReportArchive).where(
            CalcReportArchive.userId == user_id,
            CalcReportArchive.reportId == reportId,
            CalcReportArchive.type == 0,  # 临时记录
        )
    )

    # 更新默认值
    final_defaults = {}
    deep_update(final_defaults, last_archive.defaults if last_archive else {}, defaults)

    # 获取 sandbox 执行器并执行
    executor = get_sandbox_executor()

    return await executor.execute_script(
        file_path,
        final_defaults,
        is_silent=is_silent,
        package_root=package_root,
    )


async def continue_execution(
    execution_id: str,
    defaults: dict[str, dict[str, Any]],
) -> ExecutionResult:
    """
    继续计算执行
    :return: 字典，包含 execution_id 等信息
    返回值示例：
    {
        "execution_id": "some-unique-id",
        "window":{},
        "resultUrl": "public/path/to/result"
    }
    """

    logger.info(f"Continuing execution: execution_id={execution_id}")

    # 获取 sandbox 执行器并继续执行
    executor = get_sandbox_executor()
    return await executor.continue_execution(
        execution_id,
        defaults,
    )


async def start_file_execution(user_id: int, file_path: str) -> ExecutionResult:
    """
    启动文件执行（调试用）
    """

    logger.info(f"Starting file execution: file_path={file_path}")

    # 获取 sandbox 执行器并执行
    executor = get_sandbox_executor()

    (script_path, package_root) = _get_report_file_path(user_id, file_path)
    return await executor.execute_script(
        script_path,
        {},
        is_silent=True,
        package_root=package_root,
    )
