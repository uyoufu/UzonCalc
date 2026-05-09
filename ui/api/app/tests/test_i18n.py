import asyncio

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.exception.custom_exception import CustomException, raise_ex
from app.i18n import (
    _,
    DEFAULT_LOCALE,
    get_translation,
    reset_locale,
    select_locale,
    set_locale,
)
from app.middleware.i18n import i18n_middleware
from app.response.response_result import ok
from app.service.calc_report_service import copy_calc_report


def test_select_locale_uses_query_lang_first():
    locale = select_locale("zh-CN", "en-US,en;q=0.9")

    assert locale == "zh_CN"


def test_select_locale_accepts_english_query_lang():
    locale = select_locale("en", "zh-CN,zh;q=0.9")

    assert locale == "en"


def test_select_locale_uses_accept_language_when_query_missing():
    locale = select_locale(None, "zh-CN,zh;q=0.9,en;q=0.8")

    assert locale == "zh_CN"


def test_select_locale_falls_back_to_default_for_unsupported_language():
    locale = select_locale(None, "fr-FR,fr;q=0.9")

    assert locale == DEFAULT_LOCALE


def test_get_translation_uses_cache_for_same_locale():
    translation = get_translation("en")

    assert get_translation("en") is translation


def test_i18n_middleware_sets_request_locale_from_query_lang():
    app = FastAPI()

    @app.middleware("http")
    async def use_i18n(request: Request, call_next):
        return await i18n_middleware(request, call_next)

    @app.get("/locale")
    async def read_locale(request: Request):
        return {"state": request.state.locale, "context": _("Authorization failed!")}

    client = TestClient(app)

    response = client.get("/locale?lang=zh-CN")

    assert response.status_code == 200
    assert response.json() == {"state": "zh_CN", "context": "认证失败！"}


def test_i18n_middleware_falls_back_to_default_locale():
    app = FastAPI()

    @app.middleware("http")
    async def use_i18n(request: Request, call_next):
        return await i18n_middleware(request, call_next)

    @app.get("/locale")
    async def read_locale(request: Request):
        return {"state": request.state.locale, "context": _("Authorization failed!")}

    client = TestClient(app)

    response = client.get("/locale")

    assert response.status_code == 200
    assert response.json() == {"state": "en", "context": "Authorization failed!"}


def test_ok_message_uses_current_locale():
    token = set_locale("zh-CN")
    try:
        response = ok()
    finally:
        reset_locale(token)

    assert response.message == "成功"


def test_raise_ex_message_uses_current_locale():
    token = set_locale("zh-CN")
    try:
        with pytest.raises(CustomException) as exc_info:
            raise_ex("Category not found", code=404)
    finally:
        reset_locale(token)

    assert exc_info.value.model_dump()["message"] == "分类不存在"


def test_service_error_message_uses_current_locale():
    token = set_locale("zh-CN")
    try:
        with pytest.raises(CustomException) as exc_info:
            asyncio.run(
                copy_calc_report(1, "source-report", "", None)  # type: ignore[arg-type]
            )
    finally:
        reset_locale(token)

    assert exc_info.value.model_dump()["message"] == "报告名称必填"


def test_dynamic_message_keeps_placeholder_values():
    token = set_locale("zh-CN")
    try:
        message = _("Report name '{name}' already exists").format(name="demo")
    finally:
        reset_locale(token)

    assert message == "报告名称 'demo' 已存在"
