"""Validate and update all release-version file formats."""

from __future__ import annotations

import configparser
import json
import re
import tomllib
from pathlib import Path

from utils.version_update_models import (
    ProjectKey,
    ProjectUpgradePlan,
    VersionUpdateError,
)


def replace_unique(text: str, pattern: str, replacement: str, *, source: Path) -> str:
    """Replace exactly one validated version occurrence.

    Args:
        text: Original file content.
        pattern: Regular expression containing the version occurrence.
        replacement: Replacement expression or literal.
        source: File path used in errors.

    Returns:
        Updated text.

    Raises:
        VersionUpdateError: If the pattern does not match exactly once.
    """
    updated, count = re.subn(
        pattern,
        replacement,
        text,
        count=2,
        flags=re.MULTILINE | re.DOTALL,
    )
    if count != 1:
        raise VersionUpdateError(
            f"{source} 中预期存在一个版本字段，实际匹配到 {count} 个"
        )
    return updated


def update_json_version(text: str, version: str, *, source: Path) -> str:
    """Validate JSON and replace its unique top-level version field.

    Args:
        text: JSON source text.
        version: New normalized version.
        source: File path used in errors.

    Returns:
        Updated JSON text preserving unrelated formatting.

    Raises:
        VersionUpdateError: If JSON or its top-level version is invalid.
    """
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VersionUpdateError(f"无法解析 JSON 文件 {source}: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("version"), str):
        raise VersionUpdateError(f"{source} 必须包含字符串类型的顶层 version 字段")
    return replace_unique(
        text,
        r'^(\s*"version"\s*:\s*")[^"]+("\s*,?\s*)$',
        rf"\g<1>{version}\g<2>",
        source=source,
    )


def update_project_toml(text: str, version: str, *, source: Path, table: str) -> str:
    """Validate TOML and replace a version in one named table.

    Args:
        text: TOML source text.
        version: New normalized version.
        source: File path used in errors.
        table: Table containing the canonical version.

    Returns:
        Updated TOML text.

    Raises:
        VersionUpdateError: If TOML or the requested version is invalid.
    """
    try:
        document = tomllib.loads(text)
        value = document[table]["version"]
    except (tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise VersionUpdateError(f"无法解析 {source} 的 {table}.version") from exc
    if not isinstance(value, str):
        raise VersionUpdateError(f"{source} 的 {table}.version 必须是字符串")
    escaped_table = re.escape(table)
    pattern = rf'(^\[{escaped_table}\]\s*(?:(?!^\[).)*?^version\s*=\s*")[^"]+("\s*$)'
    return replace_unique(text, pattern, rf"\g<1>{version}\g<2>", source=source)


def update_ini_version(text: str, version: str, *, source: Path) -> str:
    """Validate INI and replace ``app.version`` without rewriting comments.

    Args:
        text: INI source text.
        version: New normalized version.
        source: File path used in errors.

    Returns:
        Updated INI text.

    Raises:
        VersionUpdateError: If INI or ``app.version`` is invalid.
    """
    parser = configparser.ConfigParser()
    try:
        parser.read_string(text)
        parser.get("app", "version")
    except (
        configparser.Error,
        KeyError,
        configparser.NoOptionError,
        configparser.NoSectionError,
    ) as exc:
        raise VersionUpdateError(f"无法解析 {source} 的 app.version") from exc
    pattern = r"(^\[app\]\s*(?:(?!^\[).)*?^version\s*=\s*)[^\r\n]+($)"
    return replace_unique(text, pattern, rf"\g<1>{version}\g<2>", source=source)


def update_typescript_version(text: str, version: str, *, source: Path) -> str:
    """Replace the unique TypeScript application version property.

    Args:
        text: TypeScript source text.
        version: New normalized version.
        source: File path used in errors.

    Returns:
        Updated TypeScript source.

    Raises:
        VersionUpdateError: If the property is missing or ambiguous.
    """
    return replace_unique(
        text,
        r"^(\s*version:\s*')[^']+('\s*)$",
        rf"\g<1>{version}\g<2>",
        source=source,
    )


def update_lock_package(
    text: str, package_name: str, version: str, *, source: Path
) -> str:
    """Validate a TOML lockfile and update one named local package.

    Args:
        text: Lockfile source text.
        package_name: Exact local package name.
        version: New normalized version.
        source: File path used in errors.

    Returns:
        Updated lockfile text.

    Raises:
        VersionUpdateError: If the package is missing, duplicated, or malformed.
    """
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise VersionUpdateError(f"无法解析锁文件 {source}: {exc}") from exc
    packages = [
        package
        for package in document.get("package", [])
        if isinstance(package, dict) and package.get("name") == package_name
    ]
    if len(packages) != 1 or not isinstance(packages[0].get("version"), str):
        raise VersionUpdateError(f"{source} 必须包含唯一的 {package_name} 包版本")
    escaped_name = re.escape(package_name)
    pattern = (
        rf'(^\[\[package\]\]\s*(?:(?!^\[\[package\]\]).)*?^name = "{escaped_name}"\s*'
        rf'(?:(?!^\[\[package\]\]).)*?^version = ")[^"]+("\s*$)'
    )
    return replace_unique(text, pattern, rf"\g<1>{version}\g<2>", source=source)


def build_file_updates(
    repo_root: Path, plans: list[ProjectUpgradePlan]
) -> dict[Path, bytes]:
    """Build all selected version-file contents before writing anything.

    Args:
        repo_root: Repository containing release files.
        plans: Project plans with selected target versions.

    Returns:
        Absolute paths mapped to validated replacement bytes.

    Raises:
        VersionUpdateError: If any target file cannot be read or validated.
    """
    texts: dict[Path, str] = {}

    def load(relative_path: str) -> tuple[Path, str]:
        """Load a target once so shared lockfiles accumulate multiple updates."""
        path = repo_root / relative_path
        if path not in texts:
            try:
                texts[path] = path.read_bytes().decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise VersionUpdateError(f"无法读取版本文件 {path}: {exc}") from exc
        return path, texts[path]

    for plan in plans:
        if plan.target_version is None:
            continue
        version = str(plan.target_version)
        if plan.config.key is ProjectKey.WEB:
            path, text = load("src/web/package.json")
            texts[path] = update_json_version(text, version, source=path)
            path, text = load("src/web/src/config/app.config.ts")
            texts[path] = update_typescript_version(text, version, source=path)
            path, text = load("src/web/src-tauri/Cargo.toml")
            texts[path] = update_project_toml(
                text, version, source=path, table="package"
            )
            path, text = load("src/web/src-tauri/Cargo.lock")
            texts[path] = update_lock_package(text, "UzonCalc", version, source=path)
            path, text = load("src/web/src-tauri/tauri.conf.json")
            texts[path] = update_json_version(text, version, source=path)
        elif plan.config.key is ProjectKey.API:
            path, text = load("src/api/pyproject.toml")
            texts[path] = update_project_toml(
                text, version, source=path, table="project"
            )
            path, text = load("src/api/config/app.ini")
            texts[path] = update_ini_version(text, version, source=path)
            path, text = load("uv.lock")
            texts[path] = update_lock_package(
                text, "uzoncalc-api", version, source=path
            )
        else:
            path, text = load("src/core/pyproject.toml")
            texts[path] = update_project_toml(
                text, version, source=path, table="project"
            )
            path, text = load("uv.lock")
            texts[path] = update_lock_package(text, "uzoncalc", version, source=path)
    return {path: text.encode("utf-8") for path, text in texts.items()}
