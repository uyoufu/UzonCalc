import gettext
from contextvars import ContextVar, Token
from pathlib import Path

from babel import Locale, UnknownLocaleError
from babel.core import negotiate_locale

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "zh_CN")
TRANSLATION_DOMAIN = "messages"
LOCALE_DIR = Path(__file__).resolve().parent / "locales"

_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)
_translation_cache: dict[str, gettext.NullTranslations] = {}


def normalize_locale(locale: str | None) -> str | None:
    """将请求语言标准化为项目支持的 locale 名称。"""
    if not locale:
        return None

    raw_locale = locale.strip().replace("-", "_")
    if not raw_locale:
        return None

    try:
        parsed = Locale.parse(raw_locale, sep="_")
    except (UnknownLocaleError, ValueError):
        return None

    if parsed.language == "zh":
        return "zh_CN"
    if parsed.language == "en":
        return "en"

    locale_name = str(parsed)
    if locale_name in SUPPORTED_LOCALES:
        return locale_name
    return None


def _parse_accept_language(accept_language: str | None) -> list[str]:
    if not accept_language:
        return []

    languages: list[tuple[str, float, int]] = []
    for index, item in enumerate(accept_language.split(",")):
        parts = [part.strip() for part in item.split(";")]
        language = parts[0]
        if not language:
            continue

        quality = 1.0
        for param in parts[1:]:
            key, _, value = param.partition("=")
            if key.strip() != "q":
                continue
            try:
                quality = float(value)
            except ValueError:
                quality = 0.0

        if quality > 0:
            languages.append((language, quality, index))

    languages.sort(key=lambda item: (-item[1], item[2]))
    return [language for language, _, _ in languages]


def select_locale(query_lang: str | None, accept_language: str | None) -> str:
    query_locale = normalize_locale(query_lang)
    if query_locale in SUPPORTED_LOCALES:
        return query_locale

    preferred_locales = [
        locale
        for locale in (
            normalize_locale(language) for language in _parse_accept_language(accept_language)
        )
        if locale
    ]
    locale = negotiate_locale(preferred_locales, SUPPORTED_LOCALES, sep="_")
    return locale or DEFAULT_LOCALE


def set_locale(locale: str | None) -> Token[str]:
    selected_locale = normalize_locale(locale) or DEFAULT_LOCALE
    return _current_locale.set(selected_locale)


def reset_locale(token: Token[str]) -> None:
    _current_locale.reset(token)


def get_locale() -> str:
    return _current_locale.get()


def get_translation(locale: str | None = None) -> gettext.NullTranslations:
    selected_locale = normalize_locale(locale) or DEFAULT_LOCALE
    if selected_locale not in _translation_cache:
        if selected_locale == DEFAULT_LOCALE:
            translation = gettext.NullTranslations()
        else:
            translation = gettext.translation(
                TRANSLATION_DOMAIN,
                localedir=LOCALE_DIR,
                languages=[selected_locale],
                fallback=True,
            )
        _translation_cache[selected_locale] = translation

    return _translation_cache[selected_locale]


def _(message: str) -> str:
    return get_translation(get_locale()).gettext(message)
