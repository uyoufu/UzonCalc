import os
import hashlib
from dataclasses import asdict
from typing import Optional, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_archive import CalcReportArchive
from app.sandbox.core.execution_result import ExecutionResult
from app.sandbox.core.executor_interface import ISandboxExecutor
from app.sandbox.core.executor_local import LocalSandboxExecutor
from app.sandbox.core.executor_remote import RemoteSandboxExecutor
from config import logger, app_config
from uzoncalc.utils_core.dot_dict import deep_update


_executor_instance: ISandboxExecutor | None = None


def _extract_defaults_from_windows(
    windows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    从 windows 中提取 defaults 信息
    格式转换: [{"title": str, "fields": [{"name": str, "value": Any, ...}]}]
             -> {"title": {"field_name": value, ...}}
    """
    defaults = {}
    for window in windows:
        title = window.get("title")
        fields = window.get("fields", [])
        if title and fields:
            defaults[title] = {}
            for field in fields:
                field_name = field.get("name")
                field_value = field.get("value")
                if field_name is not None:
                    defaults[title][field_name] = field_value
    return defaults


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


def _calculate_file_hash(file_path: str) -> str:
    """计算文件路径的 hash"""
    return hashlib.sha256(file_path.encode()).hexdigest()


async def _save_execution_archive(
    db_session: AsyncSession,
    user_id: int,
    defaults: dict[str, dict[str, Any]],
    report_oid: str | None = None,
    file_path_hash: str | None = None,
) -> None:
    """
    保存执行历史到 CalcReportArchive
    :param db_session: 数据库会话
    :param user_id: 用户 ID
    :param defaults: 执行收集到的参数值
    :param report_oid: 报告 ID（可选）
    :param file_path_hash: 文件路径 hash（文件执行时使用）
    """
    if not defaults:
        return

    # 查找或创建临时记录
    query = select(CalcReportArchive).where(
        CalcReportArchive.userId == user_id,
        CalcReportArchive.type == 0,  # 临时记录
    )

    if report_oid:
        query = query.where(CalcReportArchive.reportId == report_oid)
    elif file_path_hash:
        query = query.where(CalcReportArchive.name == file_path_hash)
    else:
        return

    archive = await db_session.scalar(query)

    if archive:
        # 增量更新现有记录
        deep_update(archive.defaults, defaults)
        # 标记 defaults 字段已修改，确保 SQLAlchemy 能检测到变化
        flag_modified(archive, "defaults")
    else:
        # 创建新的临时记录
        archive = CalcReportArchive(
            userId=user_id,
            status=1,
            type=0,  # 临时记录
            reportId=report_oid or 0,
            name=file_path_hash,
            defaults=defaults,
        )
        db_session.add(archive)

    await db_session.commit()


async def start_execution(
    db_session: AsyncSession,
    user_id: int,
    report_oid: str,
    defaults: dict[str, dict[str, Any]] = {},
    is_silent: bool = False,
) -> ExecutionResult:
    """
    启动计算执行
    :return: ExecutionResult，包含 execution_id、windows 和收集到的 defaults
    """

    logger.info(f"Starting execution: user={user_id}, reportId={report_oid}")

    # 根据 id 获取 CalcReport
    calc_report = await db_session.scalar(
        select(CalcReport).where(CalcReport.oid == report_oid)
    )
    if not calc_report:
        raise ValueError(f"CalcReport with id {report_oid} not found")

    # 计算脚本路径
    (file_path, package_root) = _get_report_file_path(user_id, calc_report.name)

    # 读取一次的历史输入
    last_archive = await db_session.scalar(
        select(CalcReportArchive).where(
            CalcReportArchive.userId == user_id,
            CalcReportArchive.reportId == report_oid,
            CalcReportArchive.type == 0,  # 临时记录
        )
    )

    # 更新默认值
    final_defaults = {}
    deep_update(final_defaults, last_archive.defaults if last_archive else {}, defaults)

    # 获取 sandbox 执行器并执行
    executor = get_sandbox_executor()

    result = await executor.execute_script(
        file_path,
        final_defaults,
        is_silent=is_silent,
        package_root=package_root,
    )

    # 保存执行结果到数据库（从 windows 中提取 defaults）
    extracted_defaults = _extract_defaults_from_windows(result.windows)
    if extracted_defaults:
        await _save_execution_archive(
            db_session,
            user_id,
            extracted_defaults,
            report_oid=report_oid,
        )

    return result


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


async def start_file_execution(
    db_session: AsyncSession,
    user_id: int,
    file_path: str,
    defaults: dict[str, dict[str, Any]] = {},
) -> ExecutionResult:
    """
    启动文件执行（调试用）
    :param db_session: 数据库会话
    :param user_id: 用户 ID
    :param file_path: 文件路径
    :param defaults: 参数值
    :return: ExecutionResult，包含 execution_id、windows 和收集到的 defaults
    """

    logger.info(f"Starting file execution: file_path={file_path}")

    # 计算文件路径的 hash
    file_path_hash = _calculate_file_hash(file_path)

    # 读取历史输入
    last_archive = await db_session.scalar(
        select(CalcReportArchive).where(
            CalcReportArchive.userId == user_id,
            CalcReportArchive.name == file_path_hash,
            CalcReportArchive.type == 0,  # 临时记录
        )
    )

    # 更新默认值
    final_defaults = {}
    deep_update(final_defaults, last_archive.defaults if last_archive else {}, defaults)

    # 获取 sandbox 执行器并执行
    executor = get_sandbox_executor()

    (script_path, package_root) = _get_report_file_path(user_id, file_path)
    result = await executor.execute_script(
        script_path,
        final_defaults,
        is_silent=True,
        package_root=package_root,
    )

    # 保存执行结果到数据库（从 windows 中提取 defaults）
    extracted_defaults = _extract_defaults_from_windows(result.windows)
    if extracted_defaults:
        await _save_execution_archive(
            db_session,
            user_id,
            extracted_defaults,
            file_path_hash=file_path_hash,
        )

    return result
