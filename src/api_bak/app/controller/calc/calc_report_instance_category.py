from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import (
    CategoryInfoReqDTO,
    CategoryInfoResDTO,
    DefaultCategoryReqDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_instance_category_service
from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc-report-instance-category",
    tags=["calc-report-instance-category"],
)


@router.get("/list")
async def get_all_calc_instance_categories(
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[List[CategoryInfoResDTO]]:
    categories = await calc_report_instance_category_service.get_all_categories(
        tokenPayloads.id, session
    )
    return ok(data=categories)


@router.get("/{categoryOid}")
async def get_calc_instance_category(
    categoryOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    category = await calc_report_instance_category_service.get_category_by_oid(
        tokenPayloads.id, categoryOid, session
    )
    return ok(data=category)


@router.post("/default")
async def get_or_create_default_category(
    data: DefaultCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    result = await calc_report_instance_category_service.get_or_create_default_category(
        tokenPayloads.id, data.defaultCategoryName, session
    )
    return ok(data=result)


@router.post("")
async def create_calc_instance_category(
    data: CategoryInfoReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    result = await calc_report_instance_category_service.create_category(
        tokenPayloads.id, data, session
    )
    logger.info("创建计算实例分类: userId=%s, categoryName=%s", tokenPayloads.id, data.name)
    return ok(data=result)


@router.put("/{categoryOid}")
async def update_calc_instance_category(
    categoryOid: str,
    data: CategoryInfoReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CategoryInfoResDTO]:
    result = await calc_report_instance_category_service.update_category(
        tokenPayloads.id, categoryOid, data, session
    )
    return ok(data=result)


@router.delete("/{categoryOid}")
async def delete_calc_instance_category(
    categoryOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    await calc_report_instance_category_service.delete_category(
        tokenPayloads.id, categoryOid, session
    )
    return ok()
