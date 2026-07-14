from typing import List
from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import (
    CategoryInfoReqDTO,
    CategoryInfoResDTO,
    DefaultCategoryReqDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_category_service
from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc-report-category",
    tags=["calc-report-category"],
)


@router.get("/list")
async def get_all_calc_categories(
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[List[CategoryInfoResDTO]]:
    """
    获取当前用户的所有计算分类

    **功能说明:**
    - 获取当前用户创建的所有计算分类
    - 按创建顺序排列

    **认证:**
    - 需要有效的 Authorization token

    **返回数据:**
    - 分类列表，每项包含: oid, name, description, cover, order, total
    """
    categories = await calc_report_category_service.get_all_categories(
        tokenPayloads.id, session
    )
    logger.debug(f"获取分类列表: userId={tokenPayloads.id}, count={len(categories)}")
    return ok(data=categories)


@router.get("/{categoryOid}")
async def get_calc_category(
    categoryOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    """
    获取单个计算分类详情

    **功能说明:**
    - 根据 OID 获取指定的计算分类详情
    - 只能获取自己的分类

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - categoryOid: 分类 OID

    **返回数据:**
    - 分类详细信息，包含: oid, name, description, cover, order, total

    **错误处理:**
    - 404: 分类不存在或已被删除
    """
    category = await calc_report_category_service.get_category_by_oid(
        tokenPayloads.id, categoryOid, session
    )
    logger.debug(f"获取分类详情: userId={tokenPayloads.id}, categoryOid={categoryOid}")
    return ok(data=category)


@router.post("/default")
async def get_or_create_default_category(
    data: DefaultCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    """
    获取或创建默认分类

    **功能说明:**
    - 如果用户没有任何有效分类，则使用默认名称创建一个分类后返回
    - 如果用户已有分类，则返回第一个分类（按 order 排序）

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - defaultCategoryName: 默认分类名称 (必填)

    **返回数据:**
    - 分类详细信息
    """
    result = await calc_report_category_service.get_or_create_default_category(
        tokenPayloads.id, data.defaultCategoryName, session
    )
    logger.debug(
        f"获取或创建默认分类: userId={tokenPayloads.id}, categoryOid={result.oid}"
    )
    return ok(data=result)


@router.post("")
async def create_calc_category(
    data: CategoryInfoReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    """
    创建新的计算分类

    **功能说明:**
    - 为当前用户创建新的计算分类
    - 分类名称在用户范围内唯一

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - name: 分类名称 (必填)
    - description: 分类描述 (可选)
    - cover: 分类封面 (可选)

    **返回数据:**
    - 新创建的分类详细信息
    """
    result = await calc_report_category_service.create_category(
        tokenPayloads.id, data, session
    )
    logger.info(f"创建分类: userId={tokenPayloads.id}, categoryName={data.name}")
    return ok(data=result)


@router.put("/{categoryOid}")
async def update_calc_category(
    categoryOid: str,
    data: CategoryInfoReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    """
    更新计算分类信息

    **功能说明:**
    - 更新指定分类的名称、描述和封面
    - 只能更新自己的分类

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - category_id: 分类 ID

    **请求参数:**
    - name: 分类名称
    - description: 分类描述
    - cover: 分类封面

    **返回数据:**
    - 更新后的分类详细信息
    """
    result = await calc_report_category_service.update_category(
        tokenPayloads.id, categoryOid, data, session
    )
    logger.info(f"更新分类: userId={tokenPayloads.id}, categoryOid={categoryOid}")
    return ok(data=result)


@router.post("/reorder")
async def update_calc_categories_order(
    categoryOids: list[str] = Body(...),
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """
    更新分类排序顺序

    **功能说明:**
    - 按提供的顺序重新排列分类
    - 用于拖拽排序场景

    **认证:**
    - 需要有效的 Authorization token

    **请求参数:**
    - category_ids: 分类 ID 列表（按新的顺序排列）

    **返回数据:**
    - 空响应（仅返回成功状态）
    """
    await calc_report_category_service.update_categories_order(
        tokenPayloads.id, categoryOids, session
    )
    logger.info(f"更新分类排序: userId={tokenPayloads.id}, count={len(categoryOids)}")
    return ok()


@router.delete("/{categoryId}")
async def delete_calc_category(
    categoryId: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """
    删除计算分类

    **功能说明:**
    - 删除指定分类
    - 只能删除空分类（不包含任何计算书）

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - category_id: 分类 ID

    **返回数据:**
    - 空响应（仅返回成功状态）
    """
    await calc_report_category_service.delete_category(
        tokenPayloads.id, categoryId, session
    )
    logger.info(f"删除分类: userId={tokenPayloads.id}, categoryId={categoryId}")
    return ok()
