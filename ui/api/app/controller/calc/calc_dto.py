import datetime
from typing import Any, Optional

from app.controller.dto_base import BaseDTO, PaginationDTO


class CategoryInfoReqDTO(BaseDTO):
    name: str
    description: Optional[str] = None


class CategoryInfoResDTO(CategoryInfoReqDTO):
    oid: str
    id: int
    order: int
    total: int


class CalcReportCountFilterDTO(BaseDTO):
    categoryId: Optional[int] = None
    filter: Optional[str] = None


class CalcReportListFilterDTO(CalcReportCountFilterDTO):
    pagination: PaginationDTO


class CalcReportReqDTO(BaseDTO):
    categoryId: int
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None


class CalcReportResDTO(CalcReportReqDTO):
    id: int
    oid: str
    userId: int
    createdAt: datetime.datetime
    version: int
    lastModified: datetime.datetime


# 执行计算报告请求 DTO
class CalcExecutionReqDTO(BaseDTO):
    reportOid: str
    isSilent: bool = False
    defaults: Optional[dict[str, dict[str, Any]]] = None


class CalcFileReqDTO(BaseDTO):
    filePath: str
    isSilent: Optional[bool] = False
    defaults: Optional[dict[str, dict[str, Any]]] = None


# 恢复计算执行请求 DTO
class CalcResumeReqDTO(BaseDTO):
    defaults: Optional[dict[str, dict[str, Any]]] = None


# 保存计算报告请求 DTO
class SaveCalcReportReqDTO(BaseDTO):
    # 名称必须存在
    reportName: str
    code: str
    # 若存在则更新，否则新增
    reportOid: Optional[str] = None
    # 新增时需要传递 categoryOid
    categoryOid: Optional[str] = None
