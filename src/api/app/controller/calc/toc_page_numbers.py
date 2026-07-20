"""ToC 页码计算 API。"""

from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, HTTPException

from app.controller.dto_base import BaseDTO
from app.response.response_result import ResponseResult, ok
from app.service.html_cache.html_cacher import html_cacher
from uzoncalc.service.toc_page_numbers import calculate_toc_page_numbers


class TocPageNumbersReqDTO(BaseDTO):
    """ToC 页码计算请求。"""

    documentUrl: str


router = APIRouter(
    prefix="/v1/calc",
    tags=["calc-toc-page-numbers"],
)


@router.post("/toc-page-numbers")
async def get_toc_page_numbers(
    data: TocPageNumbersReqDTO,
) -> ResponseResult[dict[str, int]]:
    """根据文档链接计算 ToC 标题页码。"""
    document_url = _resolve_public_document_url(data.documentUrl)
    page_numbers = await calculate_toc_page_numbers(document_url)
    return ok(page_numbers)


def _resolve_public_document_url(document_url: str) -> str:
    """将公开 HTML URL 解析为受控本地 file URL，拒绝外部地址。"""
    parsed_url = urlparse(document_url)
    public_path = unquote(parsed_url.path)
    if not public_path.startswith("/public/"):
        raise HTTPException(status_code=400, detail="Only public HTML is supported")

    relative_path = public_path.lstrip("/")
    target_path = html_cacher._resolve_public_html_path(relative_path)
    if target_path is None:
        raise HTTPException(status_code=400, detail="Document URL is not available")

    return Path(target_path).resolve().as_uri()
