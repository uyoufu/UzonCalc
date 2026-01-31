import os
import asyncio
from dataclasses import asdict
from typing import Optional, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_archive import CalcReportArchive
from app.sandbox.execution_result import ExecutionResult
from app.sandbox.manager import SandboxManager
from config import logger
from uzoncalc.utils_core.dot_dict import deep_update


def _get_report_file_path(user_id: int, report_name: str):
    return os.path.abspath(
        f"data/calcs/{user_id}/reports/{report_name.replace(".py","")}.py"
    )


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
    file_path = _get_report_file_path(user_id, calc_report.name)

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

    # Start sandbox execution
    return await SandboxManager.execute_script(
        file_path,
        final_defaults,
        is_silent=is_silent,
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

    return await SandboxManager.continue_execution(
        execution_id,
        defaults,
    )
