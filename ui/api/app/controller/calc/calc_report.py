"""
计算报告控制器
处理计算报告的 HTTP 请求
"""

from typing import List, cast
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import (
    CalcReportReqDTO,
    CalcReportResDTO,
    CalcReportListFilterDTO,
    CalcReportCountFilterDTO,
    SaveCalcReportReqDTO,
    CategoryInfoResDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_service
from config import logger, app_config
from utils.jwt_helper import TokenPayloads
from app.exception.custom_exception import raise_ex

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
    - 版本号自动初始化为 1
    - 修改时间自动设置为当前 UTC 时间

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - categoryId: 分类 ID (必填)
    - name: 报告名称 (必填)
    - description: 报告描述 (可选)
    - cover: 报告封面 (可选)

    **返回数据:**
    - 新创建的报告详细信息，包含 id, oid, userId, version, lastModified 等

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
    result = await calc_report_service.get_calc_report(reportOid, session)
    logger.debug(f"获取计算报告: userId={tokenPayloads.id}, reportOid={reportOid}")
    return ok(data=result)


@router.get("/{reportOid}/source-code")
async def get_calc_report_source_code(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[str]:
    """
    获取计算报告源码

    **功能说明:**
    - 读取指定报告对应的源码文件内容
    - 仅允许读取当前用户自己的报告

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - reportOid: 报告 OID

    **返回数据:**
    - 报告源码字符串

    **错误处理:**
    - 404: 报告不存在或源码文件不存在
    """
    source_code = await calc_report_service.get_calc_report_source_code(
        tokenPayloads.id, reportOid, session
    )
    logger.debug(f"获取计算报告源码: userId={tokenPayloads.id}, reportOid={reportOid}")
    return ok(data=source_code)


@router.get("/{reportOid}/category")
async def get_calc_report_category(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    """
    获取计算报告所属的分类信息

    **功能说明:**
    - 获取指定计算报告所属的分类详细信息
    - 通过 reportOid 直接获取分类，无需获取所有分类列表

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - reportOid: 报告 OID

    **返回数据:**
    - 分类详细信息，包含: oid, name, description, cover, order, total

    **错误处理:**
    - 404: 报告或分类不存在或已被删除
    """
    result = await calc_report_service.get_calc_report_category(reportOid, session)
    logger.debug(
        f"获取计算报告分类: userId={tokenPayloads.id}, reportOid={reportOid}, categoryOid={result.oid}"
    )
    return ok(data=result)


@router.post("/list")
async def list_calc_reports(
    filter_data: CalcReportListFilterDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcReportResDTO]]:
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
        "data": []
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
    return ok(data=items)


@router.post("/count")
async def count_calc_reports(
    filter_data: CalcReportCountFilterDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[int]:
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
        "data": 100
    }
    ```
    """
    total = await calc_report_service.count_calc_reports(
        tokenPayloads.id, filter_data, session
    )
    logger.debug(
        f"统计计算报告: userId={tokenPayloads.id}, categoryId={filter_data.categoryId}, total={total}"
    )
    return ok(data=total)


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
    - 每次更新时自动递增版本号
    - 每次更新时自动更新最后修改时间

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
    - 更新后的报告详细信息，包含递增后的 version 和最新的 lastModified

    **错误处理:**
    - 404: 报告或分类不存在
    """

    # 判断名称是否存在
    name_exists = await calc_report_service.check_report_name_exists(
        tokenPayloads.id,
        data.name,
        session,
        category_id=data.categoryId,
        exclude_oid=reportOid,
    )
    if name_exists:
        raise_ex(f"Duplicate report name: '{data.name}'", code=400)

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


@router.post("/save")
async def save_calc_report(
    data: SaveCalcReportReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[str]:
    """
    保存计算报告文件

    **功能说明:**
    - 保存或更新计算报告的文件内容
    - 若 reportOid 存在则更新，否则创建新报告
    - 更新时自动递增版本号和更新最后修改时间
    - 支持报告改名

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - reportName: 报告名称 (若为空，则从数据库获取)
    - reportOid: 报告 OID (可选，为空则新增)
    - categoryOid: 分类 OID (新增时必填)
    - code: 报告代码内容 (必填)

    **返回数据:**
    ```json
    {
        "ok": true,
        "data": "report-oid"
    }
    ```

    **错误处理:**
    - 400: 参数不合法
    - 404: 分类或报告不存在
    """

    if not data.reportName:
        raise_ex("reportName cannot be empty")

    # 如果是新增（没有 reportOid），必须提供 categoryOid
    if not data.reportOid and not data.categoryOid:
        raise_ex("categoryOid is required for creating new report")

    # 判断名称是否存在
    name_exists = await calc_report_service.check_report_name_exists(
        tokenPayloads.id,
        data.reportName,
        session,
        category_oid=data.categoryOid,
        exclude_oid=data.reportOid,
    )
    if name_exists:
        if data.reportOid:
            raise_ex(
                f"报告名称 '{data.reportName}' 已存在，不能与其他报告重名", code=400
            )
        else:
            raise_ex(f"报告名称 '{data.reportName}' 已存在", code=400)

    # 保存或更新数据库记录，并统一处理文件同步
    report_dto, file_path = await calc_report_service.save_calc_report_source_code(
        tokenPayloads.id,
        data.reportName,
        data.reportOid,
        data.categoryOid,
        data.code,
        session,
    )

    logger.info(
        f"保存计算报告: userId={tokenPayloads.id}, "
        f"reportOid={report_dto.oid}, reportName={data.reportName}, "
        f"filePath={file_path}"
    )

    return ok(data=report_dto.oid)
