"""Resolve release metadata and safely update localized download documents.

This module contains deterministic Git, validation, Markdown, and file-writing
logic used by ``scripts/new_version_doc.py``.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any


TARGET_VERSION_PATH = Path("src/web/src-tauri/Cargo.toml")
DOWNLOAD_FILE_NAME_TEMPLATE = "uzoncalc-win-x64-{version}.zip"
DOWNLOAD_URL_TEMPLATE = (
    "https://oss.uzoncloud.com:2234/public/files/soft/uzoncalc-win-x64-{version}.zip"
)
SEMANTIC_VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)$"
)
RELEASE_HEADING_PATTERN = re.compile(
    r"(?m)^## (?P<version>(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*))\s*$"
)
RELEASE_NOTE_HEADING_PATTERN = re.compile(r"(?m)^###\s+(.+?)\s*$")
RELEASE_NOTE_LIST_PATTERN = re.compile(r"(?m)^(?:\d+\.|[-*])\s+\S")
VersionTuple = tuple[int, int, int]


class ReleaseDocError(RuntimeError):
    """Represent an expected release-document workflow failure.

    Args:
        message: User-facing failure description.

    Returns:
        An error carrying actionable context.

    Raises:
        None.
    """


class ReleaseLanguage(StrEnum):
    """Identify a supported release-document language.

    Args:
        value: Stable key used by the OpenCode JSON payload.

    Returns:
        A Chinese or English language member.

    Raises:
        ValueError: If the value is unsupported.
    """

    CHINESE = "zh"
    ENGLISH = "en"


@dataclass(frozen=True)
class ReleaseDocumentConfig:
    """Describe one localized release document and its fixed labels.

    Args:
        relative_path: Document path relative to the repository root.
        date_label: Localized release-date label.
        date_separator: Punctuation between the date label and value.
        download_heading: Localized download-section heading.
        allowed_note_headings: Allowed AI-generated category headings.

    Returns:
        Immutable localized document configuration.

    Raises:
        None.
    """

    relative_path: Path
    date_label: str
    date_separator: str
    download_heading: str
    allowed_note_headings: frozenset[str]


@dataclass(frozen=True)
class ReleaseContext:
    """Hold the resolved Git range and target release metadata.

    Args:
        previous_tag: Latest reachable semantic-version release tag.
        target_version: Desktop package version being documented.
        release_date: Local ISO date used in generated sections.
        commit_subjects: Oldest-first subjects after the release tag.

    Returns:
        Immutable generation context.

    Raises:
        None.
    """

    previous_tag: str
    target_version: str
    release_date: str
    commit_subjects: tuple[str, ...]


DOCUMENT_CONFIGS: dict[ReleaseLanguage, ReleaseDocumentConfig] = {
    ReleaseLanguage.CHINESE: ReleaseDocumentConfig(
        Path("src/docs/src/downloads.md"),
        "更新日期",
        "：",
        "下载地址",
        frozenset({"功能新增", "功能优化", "Bug 修复"}),
    ),
    ReleaseLanguage.ENGLISH: ReleaseDocumentConfig(
        Path("src/docs/src/en/downloads.md"),
        "Release date",
        ": ",
        "Download",
        frozenset({"New Features", "Improvements", "Bug Fixes"}),
    ),
}


def parse_semantic_version(version_text: str, *, source: str) -> VersionTuple:
    """Parse strict ``major.minor.patch`` text for comparison.

    Args:
        version_text: Version without a ``v`` prefix.
        source: Description included in validation errors.

    Returns:
        Numeric major, minor, and patch components.

    Raises:
        ReleaseDocError: If the version is invalid.
    """
    match = SEMANTIC_VERSION_PATTERN.fullmatch(version_text.strip())
    if match is None:
        raise ReleaseDocError(
            f"{source} 版本号必须为 major.minor.patch: {version_text}"
        )
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def read_target_version(repo_root: Path) -> str:
    """Read the desktop artifact version from the Tauri manifest.

    Args:
        repo_root: Repository containing the manifest.

    Returns:
        Validated desktop semantic version.

    Raises:
        ReleaseDocError: If the manifest or version is invalid.
    """
    manifest_path = repo_root / TARGET_VERSION_PATH
    try:
        with manifest_path.open("rb") as manifest_file:
            version: Any = tomllib.load(manifest_file)["package"]["version"]
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise ReleaseDocError(f"无法读取桌面版本源 {manifest_path}: {exc}") from exc
    if not isinstance(version, str):
        raise ReleaseDocError(f"桌面版本源不是字符串: {manifest_path}")
    parse_semantic_version(version, source=str(TARGET_VERSION_PATH))
    return version


def validate_release_notes(language: ReleaseLanguage, content: str) -> str:
    """Validate an AI note body and reject script-owned fields.

    Args:
        language: Language selecting allowed headings.
        content: Markdown body supplied by OpenCode.

    Returns:
        Trimmed valid Markdown.

    Raises:
        ReleaseDocError: If the body is empty or malformed.
    """
    notes = content.strip()
    if not notes:
        raise ReleaseDocError(f"{language.value} 发布说明不能为空。")
    forbidden_patterns = (
        re.compile(r"(?m)^##\s+"),
        re.compile(r"(?mi)^>\s*(?:更新日期|release date)\s*[:：]"),
        re.compile(r"(?mi)^###\s*(?:下载地址|downloads?)\s*$"),
        re.compile(r"uzoncalc-win-x64-\d+\.\d+\.\d+\.zip", re.IGNORECASE),
        re.compile(r"(?m)^---\s*$"),
    )
    if any(pattern.search(notes) for pattern in forbidden_patterns):
        raise ReleaseDocError(
            f"{language.value} 只能包含更新正文，不能包含版本、日期或下载信息。"
        )
    headings = RELEASE_NOTE_HEADING_PATTERN.findall(notes)
    allowed_headings = DOCUMENT_CONFIGS[language].allowed_note_headings
    if not headings or any(heading not in allowed_headings for heading in headings):
        expected = "、".join(sorted(allowed_headings))
        raise ReleaseDocError(
            f"{language.value} 发布说明必须使用允许的三级标题: {expected}。"
        )
    if RELEASE_NOTE_LIST_PATTERN.search(notes) is None:
        raise ReleaseDocError(f"{language.value} 发布说明至少需要一个列表项。")
    return notes


def parse_release_notes_payload(payload_text: str) -> dict[ReleaseLanguage, str]:
    """Parse bilingual note bodies supplied through standard input.

    Args:
        payload_text: JSON object containing ``zh`` and ``en`` strings.

    Returns:
        Validated note body for each language.

    Raises:
        ReleaseDocError: If JSON shape or content is invalid.
    """
    try:
        payload: Any = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ReleaseDocError(f"OpenCode 提交的发布说明不是有效 JSON: {exc}") from exc
    expected_keys = {language.value for language in ReleaseLanguage}
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise ReleaseDocError("发布说明 JSON 必须且只能包含 zh 和 en 字段。")
    notes: dict[ReleaseLanguage, str] = {}
    for language in ReleaseLanguage:
        content = payload[language.value]
        if not isinstance(content, str):
            raise ReleaseDocError(f"{language.value} 发布说明必须是字符串。")
        notes[language] = validate_release_notes(language, content)
    return notes


def build_release_section(
    language: ReleaseLanguage, version: str, release_date: str, notes: str
) -> str:
    """Combine AI notes with script-owned release metadata.

    Args:
        language: Language selecting localized labels.
        version: Target desktop version.
        release_date: ISO-formatted local date.
        notes: Validated localized note body.

    Returns:
        Complete Markdown release section.

    Raises:
        None.
    """
    config = DOCUMENT_CONFIGS[language]
    file_name = DOWNLOAD_FILE_NAME_TEMPLATE.format(version=version)
    download_url = DOWNLOAD_URL_TEMPLATE.format(version=version)
    return (
        f"## {version}\n\n"
        f"> {config.date_label}{config.date_separator}{release_date}\n\n"
        f"{notes}\n\n"
        f"### {config.download_heading}\n\n"
        f"[{file_name}]({download_url})"
    )


def upsert_release_section(document: str, version: str, section: str) -> str:
    """Insert or replace one release while preserving older content.

    Args:
        document: Existing downloads Markdown.
        version: Release version to upsert.
        section: Complete replacement section.

    Returns:
        Updated document containing one target section.

    Raises:
        ReleaseDocError: If frontmatter or version headings are invalid.
    """
    if not document.startswith("---\n"):
        raise ReleaseDocError("下载文档缺少起始 frontmatter。")
    frontmatter_end = document.find("\n---\n", 4)
    if frontmatter_end < 0:
        raise ReleaseDocError("下载文档 frontmatter 未正确结束。")
    headings = list(RELEASE_HEADING_PATTERN.finditer(document))
    targets = [heading for heading in headings if heading.group("version") == version]
    if len(targets) > 1:
        raise ReleaseDocError(f"下载文档中存在重复版本标题: {version}")
    if targets:
        target = targets[0]
        start = target.start()
        following = [heading for heading in headings if heading.start() > start]
        end = following[0].start() if following else len(document)
    else:
        start = headings[0].start() if headings else frontmatter_end + len("\n---\n")
        end = start
    before = document[:start].rstrip("\n")
    after = document[end:].lstrip("\n")
    updated = f"{before}\n\n{section.strip()}"
    if after:
        updated = f"{updated}\n\n{after}"
    return f"{updated.rstrip()}\n"


def write_text_atomically(path: Path, content: str) -> None:
    """Replace one UTF-8 file through a sibling temporary file.

    Args:
        path: Destination path.
        content: Complete text to store.

    Returns:
        None.

    Raises:
        OSError: If writing or replacing fails.
    """
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def read_release_documents(repo_root: Path) -> dict[Path, str]:
    """Read both localized documents as rollback snapshots.

    Args:
        repo_root: Repository containing the documents.

    Returns:
        Absolute document paths mapped to current content.

    Raises:
        ReleaseDocError: If either document cannot be read.
    """
    documents: dict[Path, str] = {}
    for config in DOCUMENT_CONFIGS.values():
        path = repo_root / config.relative_path
        try:
            documents[path] = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ReleaseDocError(f"无法读取下载文档 {path}: {exc}") from exc
    return documents


def restore_release_documents(snapshots: dict[Path, str]) -> None:
    """Restore exact snapshots after a failed generation attempt.

    Args:
        snapshots: Absolute paths mapped to original content.

    Returns:
        None.

    Raises:
        ReleaseDocError: If restoration fails.
    """
    try:
        for path, content in snapshots.items():
            write_text_atomically(path, content)
    except OSError as exc:
        raise ReleaseDocError(f"恢复下载文档失败: {exc}") from exc


def apply_release_notes(
    repo_root: Path, payload_text: str, *, local_date: date | None = None
) -> None:
    """Validate AI notes and upsert both localized documents.

    Args:
        repo_root: Repository containing version sources and documents.
        payload_text: Bilingual JSON note bodies.
        local_date: Optional date override used by tests.

    Returns:
        None.

    Raises:
        ReleaseDocError: If validation, rendering, or writing fails.
    """
    version = read_target_version(repo_root)
    release_date = (local_date or date.today()).isoformat()
    notes = parse_release_notes_payload(payload_text)
    snapshots = read_release_documents(repo_root)
    updates: dict[Path, str] = {}
    for language, config in DOCUMENT_CONFIGS.items():
        path = repo_root / config.relative_path
        section = build_release_section(
            language, version, release_date, notes[language]
        )
        updates[path] = upsert_release_section(snapshots[path], version, section)
    try:
        for path, content in updates.items():
            write_text_atomically(path, content)
    except OSError as exc:
        restore_release_documents(snapshots)
        raise ReleaseDocError(f"写入下载文档失败: {exc}") from exc


def verify_release_documents(repo_root: Path, context: ReleaseContext) -> None:
    """Verify both documents contain the expected generated metadata.

    Args:
        repo_root: Repository containing generated documents.
        context: Expected version and date.

    Returns:
        None.

    Raises:
        ReleaseDocError: If either document fails postconditions.
    """
    documents = read_release_documents(repo_root)
    file_name = DOWNLOAD_FILE_NAME_TEMPLATE.format(version=context.target_version)
    for language, config in DOCUMENT_CONFIGS.items():
        content = documents[repo_root / config.relative_path]
        expected = (
            f"## {context.target_version}",
            f"> {config.date_label}{config.date_separator}{context.release_date}",
            f"### {config.download_heading}",
            file_name,
        )
        if not all(value in content for value in expected):
            raise ReleaseDocError(f"OpenCode 未正确生成 {language.value} 下载文档。")
