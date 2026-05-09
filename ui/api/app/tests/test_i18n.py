from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.i18n import _, DEFAULT_LOCALE, get_translation, select_locale
from app.middleware.i18n import i18n_middleware


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
