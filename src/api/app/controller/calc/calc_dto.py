import datetime
from typing import Any, Optional

from app.controller.dto_base import BaseDTO, PaginationDTO
from app.sandbox.core.execution_result import ExecutionResult
from app.service.html_cache.html_cacher import (
    HtmlUpdateType,
)


class CategoryInfoReqDTO(BaseDTO):
    name: str
    description: Optional[str] = None


class CategoryInfoResDTO(CategoryInfoReqDTO):
    oid: str
    id: int
    order: int
    total: int


class DefaultCategoryReqDTO(BaseDTO):
    defaultCategoryName: str


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


class CopyCalcReportReqDTO(BaseDTO):
    name: str


class CalcReportResDTO(CalcReportReqDTO):
    id: int
    oid: str
    userId: int
    createdAt: datetime.datetime
    version: int
    lastModified: datetime.datetime


class CalcReportInstanceCountFilterDTO(BaseDTO):
    categoryId: Optional[int] = None
    filter: Optional[str] = None


class CalcReportInstanceListFilterDTO(CalcReportInstanceCountFilterDTO):
    pagination: PaginationDTO


class CalcReportInstanceReqDTO(BaseDTO):
    categoryId: int
    name: str
    description: Optional[str] = None


class CalcReportInstanceSaveReqDTO(CalcReportInstanceReqDTO):
    reportOid: str
    defaults: dict[str, dict[str, Any]] = {}
    resultPath: str


class CalcReportInstanceResDTO(CalcReportInstanceReqDTO):
    id: int
    oid: str
    userId: int
    reportId: int
    reportOid: str
    reportName: Optional[str] = None
    defaults: dict[str, dict[str, Any]] = {}
    resultPath: Optional[str] = None
    createdAt: datetime.datetime
    version: int
    lastModified: datetime.datetime


# 执行计算报告请求 DTO
class CalcExecutionReqDTO(BaseDTO):
    reportOid: str
    isSilent: bool = False
    defaults: Optional[dict[str, dict[str, Any]]] = None
    # 上一次已渲染的 HTML 路径，用于判断是否可进行正文增量更新
    lastHtmlPath: Optional[str] = None


class CalcFileReqDTO(BaseDTO):
    filePath: str
    isSilent: Optional[bool] = False
    defaults: Optional[dict[str, dict[str, Any]]] = None
    # 上一次已渲染的 HTML 路径，用于判断是否可进行正文增量更新
    lastHtmlPath: Optional[str] = None


# 恢复计算执行请求 DTO
class CalcResumeReqDTO(BaseDTO):
    defaults: Optional[dict[str, dict[str, Any]]] = None
    # 上一次已渲染的 HTML 路径，用于判断是否可进行正文增量更新
    lastHtmlPath: Optional[str] = None


class ExecutionResultResDTO(ExecutionResult):
    """计算执行结果响应 DTO"""

    # 缓存后的 HTML 相对路径
    htmlPath: str = ""
    # 前端 iframe 更新类型：0 无变化，1 全量变化，2 局部变化
    updateType: HtmlUpdateType = HtmlUpdateType.Full
    # HTML 正文增量补丁，存在时前端可复用当前 iframe
    htmlContentPatch: Optional[str] = None


# 保存计算报告请求 DTO
class SaveCalcReportReqDTO(BaseDTO):
    # 名称必须存在
    reportName: str
    code: str
    # 若存在则更新，否则新增
    reportOid: Optional[str] = None
    # 新增时需要传递 categoryOid
    categoryOid: Optional[str] = None
