"""
计算报告控制器
处理计算报告的 HTTP 请求
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import (
    CalcReportReqDTO,
    CalcReportResDTO,
    CalcReportListFilterDTO,
    CalcReportCountFilterDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_service
from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc-report",
    tags=["calc-report"],
)


@router.post("")
async def create_calc_report(
    data: CalcReportReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """
    创建新的计算报告

    **功能说明:**
    - 为当前用户创建新的计算报告
    - 创建时自动向分类计数中累加 1
    - 分类必须存在且属于当前用户

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - categoryId: 分类 ID (必填)
    - name: 报告名称 (必填)
    - description: 报告描述 (可选)
    - cover: 报告封面 (可选)

    **返回数据:**
    - 新创建的报告详细信息，包含 id, oid, userId 等

    **错误处理:**
    - 404: 分类不存在或已被删除
    """
    result = await calc_report_service.create_calc_report(
        tokenPayloads.id, data, session
    )
    logger.info(
        f"创建计算报告: userId={tokenPayloads.id}, categoryId={data.categoryId}, name={data.name}"
    )
    return ok(data=result)


@router.get("/{reportOid}")
async def get_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """
    获取单个计算报告详情

    **功能说明:**
    - 获取指定的计算报告详细信息
    - 只能获取自己的报告

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - reportOid: 报告 OID

    **返回数据:**
    - 报告详细信息

    **错误处理:**
    - 404: 报告不存在或已被删除
    """
    result = await calc_report_service.get_calc_report(
        tokenPayloads.id, reportOid, session
    )
    logger.debug(f"获取计算报告: userId={tokenPayloads.id}, reportOid={reportOid}")
    return ok(data=result)


@router.post("/list")
async def list_calc_reports(
    filter_data: CalcReportListFilterDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[dict]:
    """
    获取计算报告列表（分页）

    **功能说明:**
    - 获取当前用户的计算报告列表
    - 支持按分类筛选
    - 支持分页

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - categoryId: 分类 ID (可选，按分类筛选)
    - filter: 搜索关键词 (预留，暂未实现)
    - pagination:
      - skip: 跳过的记录数 (默认 0)
      - limit: 返回的记录数 (默认 10)
      - sortBy: 排序字段 (默认 id)
      - descending: 是否降序 (默认 true)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "items": [...],
            "total": 100,
            "skip": 0,
            "limit": 10
        }
    }
    ```

    **错误处理:**
    - 400: 请求参数错误
    """
    items, total = await calc_report_service.list_calc_reports(
        tokenPayloads.id, filter_data, session
    )
    logger.debug(
        f"获取计算报告列表: userId={tokenPayloads.id}, categoryId={filter_data.categoryId}, count={len(items)}"
    )
    return ok(
        data={
            "items": items,
            "total": total,
            "skip": filter_data.pagination.skip,
            "limit": filter_data.pagination.limit,
        }
    )


@router.post("/count")
async def count_calc_reports(
    filter_data: CalcReportCountFilterDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[dict]:
    """
    统计计算报告数量

    **功能说明:**
    - 统计当前用户的计算报告总数
    - 支持按分类筛选

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - categoryId: 分类 ID (可选，按分类筛选)
    - filter: 搜索关键词 (预留，暂未实现)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "total": 100
        }
    }
    ```
    """
    total = await calc_report_service.count_calc_reports(
        tokenPayloads.id, filter_data, session
    )
    logger.debug(
        f"统计计算报告: userId={tokenPayloads.id}, categoryId={filter_data.categoryId}, total={total}"
    )
    return ok(data={"total": total})


@router.put("/{reportOid}")
async def update_calc_report(
    reportOid: str,
    data: CalcReportReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """
    更新计算报告

    **功能说明:**
    - 更新指定报告的信息
    - 只能更新自己的报告
    - 支持修改分类，分类变化时自动更新两个分类的计数

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - reportOid: 报告 OID

    **请求参数:**
    - categoryId: 分类 ID (必填)
    - name: 报告名称 (必填)
    - description: 报告描述 (可选)
    - cover: 报告封面 (可选)

    **返回数据:**
    - 更新后的报告详细信息

    **错误处理:**
    - 404: 报告或分类不存在
    """
    result = await calc_report_service.update_calc_report(
        tokenPayloads.id, reportOid, data, session
    )
    logger.info(f"更新计算报告: userId={tokenPayloads.id}, reportOid={reportOid}")
    return ok(data=result)


@router.delete("/{reportOid}")
async def delete_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """
    删除计算报告（逻辑删除）

    **功能说明:**
    - 删除指定的计算报告
    - 执行逻辑删除：将 status 设为 0
    - 删除时自动向分类计数中减少 1
    - 只能删除自己的报告

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - reportOid: 报告 OID

    **返回数据:**
    - 成功返回空数据

    **错误处理:**
    - 404: 报告不存在或已被删除
    """
    await calc_report_service.delete_calc_report(tokenPayloads.id, reportOid, session)
    logger.info(f"删除计算报告: userId={tokenPayloads.id}, reportOid={reportOid}")
    return ok()


@router.post("/batch-delete")
async def batch_delete_calc_reports(
    report_oids: List[str],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[dict]:
    """
    批量删除计算报告（逻辑删除）

    **功能说明:**
    - 批量删除计算报告
    - 执行逻辑删除：将 status 设为 0
    - 删除时自动更新所有涉及分类的计数
    - 只能删除自己的报告

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - report_oids: 报告 OID 列表

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": {
            "deleted": 5
        }
    }
    ```

    **错误处理:**
    - 400: 报告 OID 列表为空
    """
    deleted_count = await calc_report_service.batch_delete_calc_reports(
        tokenPayloads.id, report_oids, session
    )
    logger.info(f"批量删除计算报告: userId={tokenPayloads.id}, count={deleted_count}")
    return ok(data={"deleted": deleted_count})
