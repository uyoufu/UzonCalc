"""
计算实例控制器
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import (
    CalcReportInstanceCountFilterDTO,
    CalcReportInstanceListFilterDTO,
    CalcReportInstanceReqDTO,
    CalcReportInstanceResDTO,
    CalcReportInstanceSaveReqDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_instance_service
from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc-report-instance",
    tags=["calc-report-instance"],
)


@router.get("/{instanceOid}")
async def get_calc_report_instance(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportInstanceResDTO]:
    result = await calc_report_instance_service.get_calc_report_instance(
        tokenPayloads.id, instanceOid, session
    )
    return ok(data=result)


@router.post("/list")
async def list_calc_report_instances(
    filter_data: CalcReportInstanceListFilterDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcReportInstanceResDTO]]:
    items, total = await calc_report_instance_service.list_calc_report_instances(
        tokenPayloads.id, filter_data, session
    )
    logger.debug(
        "获取计算实例列表: userId=%s, categoryId=%s, count=%s",
        tokenPayloads.id,
        filter_data.categoryId,
        total,
    )
    return ok(data=items)


@router.post("/count")
async def count_calc_report_instances(
    filter_data: CalcReportInstanceCountFilterDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[int]:
    total = await calc_report_instance_service.count_calc_report_instances(
        tokenPayloads.id, filter_data, session
    )
    return ok(data=total)


@router.post("")
async def save_calc_report_instance(
    data: CalcReportInstanceSaveReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportInstanceResDTO]:
    result = await calc_report_instance_service.save_calc_report_instance(
        tokenPayloads.id, data, session
    )
    return ok(data=result)


@router.put("/{instanceOid}")
async def update_calc_report_instance_info(
    instanceOid: str,
    data: CalcReportInstanceReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportInstanceResDTO]:
    result = await calc_report_instance_service.update_calc_report_instance_info(
        tokenPayloads.id, instanceOid, data, session
    )
    return ok(data=result)


@router.put("/{instanceOid}/result")
async def update_calc_report_instance_result(
    instanceOid: str,
    data: CalcReportInstanceSaveReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportInstanceResDTO]:
    result = await calc_report_instance_service.update_calc_report_instance_result(
        tokenPayloads.id, instanceOid, data, session
    )
    return ok(data=result)


@router.delete("/{instanceOid}")
async def delete_calc_report_instance(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    await calc_report_instance_service.delete_calc_report_instance(
        tokenPayloads.id, instanceOid, session
    )
    return ok()
