"""
临时文件服务

提供临时文件的创建、查询和删除功能
"""

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.tmp_file import TmpFile
from config import logger


async def _delete_physical_file(file_path: str) -> bool:
    """
    删除物理文件或目录

    :param file_path: 文件路径（绝对路径）
    :return: 是否删除成功
    """
    try:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            if file_path_obj.is_dir():
                shutil.rmtree(file_path_obj)
                logger.info(f"已删除目录: {file_path}")
            else:
                file_path_obj.unlink()
                logger.info(f"已删除文件: {file_path}")

                # 检查父目录是否为空，如果为空则删除
                parent_dir = file_path_obj.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    logger.info(f"已删除空目录: {parent_dir}")
        return True
    except Exception as e:
        logger.error(f"删除文件失败 [{file_path}]，错误信息：{str(e)}")
        return False


async def create_tmp_file(
    file_path: str,
    session: AsyncSession,
    expire_time: Optional[datetime] = None,
    remark: Optional[str] = None,
) -> Optional[TmpFile]:
    """
    创建临时文件记录

    如果过期时间已经过期，文件会被立即删除

    :param file_path: 文件路径（绝对路径）
    :param session: 数据库会话
    :param expire_time: 过期时间（UTC时间），默认为1小时后
    :param remark: 备注信息
    :return: TmpFile 模型对象，如果立即被删除则返回 None
    """
    # 计算过期时间，默认为1小时后
    if expire_time is None:
        expire_time = datetime.now(timezone.utc) + timedelta(hours=1)

    # 获取当前时间
    now = datetime.now(timezone.utc)

    # 检查是否已存在相同的 file_path 记录
    existing_tmp_file = await get_tmp_file(file_path, session)
    if existing_tmp_file is not None:
        # 如果已存在，则删除旧记录
        await session.delete(existing_tmp_file)
        await session.commit()

    # 如果过期时间已经过期，立即删除文件并返回 None
    if expire_time <= now:
        await _delete_physical_file(file_path)
        logger.info(f"临时文件已立即删除（已过期）: {file_path}")
        return None

    # 创建新的临时文件记录
    tmp_file = TmpFile(
        file_path=file_path,
        expire_time=expire_time,
        remark=remark,
        is_deleted=False,
    )

    # 添加到数据库
    session.add(tmp_file)
    await session.commit()
    await session.refresh(tmp_file)

    return tmp_file


async def get_tmp_file(
    file_path: str,
    session: AsyncSession,
) -> Optional[TmpFile]:
    """
    根据文件路径查询临时文件记录

    :param file_path: 文件路径（绝对路径）
    :param session: 数据库会话
    :return: TmpFile 模型对象或 None
    """
    stmt = select(TmpFile).where(TmpFile.file_path == file_path)
    tmp_file = await session.scalar(stmt)
    return tmp_file


async def clean_expired_tmp_files(session: AsyncSession) -> tuple[int, int]:
    """
    清理所有过期的临时文件

    删除过期的物理文件和数据库记录

    :param session: 数据库会话
    :return: (成功删除数, 失败数)
    """
    # 查询所有未删除且已过期的临时文件
    current_time = datetime.now(timezone.utc)

    stmt = select(TmpFile).where(
        and_(TmpFile.is_deleted == False, TmpFile.expire_time <= current_time)
    )
    expired_files = (await session.scalars(stmt)).all()

    logger.info(f"找到过期临时文件数量：{len(expired_files)}")

    deleted_count = 0
    failed_count = 0

    for tmp_file in expired_files:
        # 删除物理文件
        is_deleted = await _delete_physical_file(tmp_file.file_path)

        if not is_deleted:
            failed_count += 1
            continue

        # 直接从数据库删除记录
        await session.delete(tmp_file)
        deleted_count += 1

    # 提交数据库更改
    await session.commit()

    logger.info(f"临时文件清理完成 - 成功: {deleted_count}, 失败: {failed_count}")
    return deleted_count, failed_count


async def delete_tmp_file(
    file_path: str,
    session: AsyncSession,
    delete_physical: bool = True,
) -> bool:
    """
    删除临时文件记录和物理文件

    :param file_path: 文件路径（绝对路径）
    :param session: 数据库会话
    :param delete_physical: 是否删除物理文件，默认为 True
    :return: 是否删除成功
    """
    # 查询数据库中的记录
    tmp_file = await get_tmp_file(file_path, session)

    if tmp_file is None:
        logger.warning(f"临时文件记录不存在: {file_path}")
        return False

    # 删除物理文件
    if delete_physical:
        success = await _delete_physical_file(file_path)
        if not success:
            return False

    # 直接从数据库删除记录
    await session.delete(tmp_file)
    await session.commit()

    logger.info(f"已删除临时文件记录: {file_path}")
    return True
