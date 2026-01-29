from typing import Optional

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
