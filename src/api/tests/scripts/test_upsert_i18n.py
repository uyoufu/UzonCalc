"""Tests for the API gettext catalog update script."""

from __future__ import annotations

import gettext
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from babel.messages.pofile import read_po

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "upsert_i18n.py"


@pytest.fixture
def upsert_i18n_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the update script as a module for focused unit tests.

    Args:
        monkeypatch: Pytest helper used to expose the sibling scripts directory.

    Returns:
        The loaded ``upsert_i18n`` script module.

    Raises:
        pytest.skip.Exception: If the planned script does not exist yet.
        pytest.fail.Exception: If the script exists but cannot load.
    """
    if not SCRIPT_PATH.is_file():
        pytest.skip(f"Planned API i18n script does not exist yet: {SCRIPT_PATH}")

    monkeypatch.syspath_prepend(str(SCRIPT_PATH.parent))
    module_name = "uzoncalc_api_upsert_i18n"
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"Unable to load API i18n script: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_upsert_i18n_script_exists() -> None:
    """The planned API i18n update script should exist."""
    assert SCRIPT_PATH.is_file(), f"Missing planned API i18n script: {SCRIPT_PATH}"


def create_test_catalog(tmp_path: Path) -> Path:
    """Create a minimal Chinese gettext catalog in the runtime directory layout.

    Args:
        tmp_path: Temporary test directory supplied by pytest.

    Returns:
        Path to the generated ``messages.po`` file.

    Raises:
        OSError: If the temporary catalog cannot be created.
    """
    po_path = tmp_path / "locales" / "zh_CN" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True)
    po_path.write_text(
        """msgid ""
msgstr ""
"Project-Id-Version: uzoncalc-api-test 1.0\\n"
"Language: zh_CN\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"

msgid "Existing message"
msgstr "现有消息"
""",
        encoding="utf-8",
    )
    return po_path


def read_catalog_message(po_path: Path, message_id: str) -> str | None:
    """Read one translated string from a PO file.

    Args:
        po_path: PO catalog path.
        message_id: Gettext message identifier to look up.

    Returns:
        The translated string, or ``None`` when the entry does not exist.

    Raises:
        OSError: If the PO file cannot be read.
    """
    with po_path.open("r", encoding="utf-8") as po_file:
        catalog = read_po(po_file, locale="zh_CN")

    message = catalog.get(message_id)
    return None if message is None else message.string


def test_update_catalog_upserts_batch_and_compiles_mo(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """Batch updates should write the PO file and a loadable MO catalog."""
    po_path = create_test_catalog(tmp_path)

    has_changes = upsert_i18n_module.update_catalog(
        po_path=po_path,
        pairs=[
            ("Existing message", "更新后的消息"),
            ("Report name '{name}' already exists", "报告名称 '{name}' 已存在"),
        ],
        delete_message_ids=[],
    )

    assert has_changes is True
    assert read_catalog_message(po_path, "Existing message") == "更新后的消息"
    mo_path = po_path.with_suffix(".mo")
    assert mo_path.is_file()

    translation = gettext.translation(
        "messages",
        localedir=po_path.parents[2],
        languages=["zh_CN"],
    )
    assert translation.gettext("Existing message") == "更新后的消息"
    assert (
        translation.gettext("Report name '{name}' already exists")
        == "报告名称 '{name}' 已存在"
    )


def test_update_catalog_deletes_existing_and_ignores_missing_message_ids(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """Deletion should remove existing entries while tolerating missing entries."""
    po_path = create_test_catalog(tmp_path)

    has_changes = upsert_i18n_module.update_catalog(
        po_path=po_path,
        pairs=[],
        delete_message_ids=["Existing message", "Missing message"],
    )

    assert has_changes is True
    assert read_catalog_message(po_path, "Existing message") is None
    translation = gettext.translation(
        "messages",
        localedir=po_path.parents[2],
        languages=["zh_CN"],
    )
    assert translation.gettext("Existing message") == "Existing message"


def test_update_catalog_does_not_rewrite_unchanged_files(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """An ineffective update should preserve both catalog files byte for byte."""
    po_path = create_test_catalog(tmp_path)
    mo_path = po_path.with_suffix(".mo")
    mo_path.write_bytes(b"existing compiled catalog")
    original_po = po_path.read_bytes()
    original_mo = mo_path.read_bytes()

    has_changes = upsert_i18n_module.update_catalog(
        po_path=po_path,
        pairs=[("Existing message", "现有消息")],
        delete_message_ids=[],
    )

    assert has_changes is False
    assert po_path.read_bytes() == original_po
    assert mo_path.read_bytes() == original_mo


def test_update_catalog_does_not_rewrite_when_all_delete_targets_are_missing(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """Missing deletion targets should not rewrite or compile the catalog."""
    po_path = create_test_catalog(tmp_path)
    mo_path = po_path.with_suffix(".mo")
    mo_path.write_bytes(b"existing compiled catalog")
    original_po = po_path.read_bytes()
    original_mo = mo_path.read_bytes()

    has_changes = upsert_i18n_module.update_catalog(
        po_path=po_path,
        pairs=[],
        delete_message_ids=["Missing message"],
    )

    assert has_changes is False
    assert po_path.read_bytes() == original_po
    assert mo_path.read_bytes() == original_mo


def test_update_catalog_rejects_placeholder_mismatch_before_writing(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """Placeholder mismatches should fail without changing PO or MO files."""
    po_path = create_test_catalog(tmp_path)
    mo_path = po_path.with_suffix(".mo")
    mo_path.write_bytes(b"existing compiled catalog")
    original_po = po_path.read_bytes()
    original_mo = mo_path.read_bytes()

    with pytest.raises(ValueError, match="placeholder"):
        upsert_i18n_module.update_catalog(
            po_path=po_path,
            pairs=[("Failed to save {name}", "保存 {file_name} 失败")],
            delete_message_ids=[],
        )

    assert po_path.read_bytes() == original_po
    assert mo_path.read_bytes() == original_mo


def test_update_catalog_round_trips_quotes_backslashes_and_newlines(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """Babel serialization should preserve complex gettext message content."""
    po_path = create_test_catalog(tmp_path)
    message_id = 'Path "{path}" failed:\nTry C:\\temp'
    translation = "路径“{path}”失败：\n请检查 C:\\temp"

    upsert_i18n_module.update_catalog(
        po_path=po_path,
        pairs=[(message_id, translation)],
        delete_message_ids=[],
    )

    assert read_catalog_message(po_path, message_id) == translation


def test_parse_args_rejects_mixed_update_and_delete_modes(
    upsert_i18n_module: ModuleType,
) -> None:
    """The CLI should reject mixing batch updates and deletions."""
    with pytest.raises(SystemExit) as exc_info:
        upsert_i18n_module.parse_args(
            ["--pair", "Existing message", "现有消息", "--delete", "Existing message"]
        )

    assert exc_info.value.code == 2


def test_update_catalog_rejects_blank_values(
    tmp_path: Path,
    upsert_i18n_module: ModuleType,
) -> None:
    """Blank message identifiers or translations should be rejected."""
    po_path = create_test_catalog(tmp_path)

    with pytest.raises(ValueError, match="cannot be blank"):
        upsert_i18n_module.update_catalog(
            po_path=po_path,
            pairs=[("", "空消息")],
            delete_message_ids=[],
        )


def test_main_supports_custom_po_file_and_reports_compilation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    upsert_i18n_module: ModuleType,
) -> None:
    """The CLI entrypoint should update a custom PO file and report its MO path."""
    po_path = create_test_catalog(tmp_path)

    exit_code = upsert_i18n_module.main(
        [
            "--po-file",
            str(po_path),
            "--pair",
            "New message",
            "新消息",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(po_path) in captured.out
    assert str(po_path.with_suffix(".mo")) in captured.out
    assert read_catalog_message(po_path, "New message") == "新消息"


def test_main_reports_malformed_po_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    upsert_i18n_module: ModuleType,
) -> None:
    """Malformed PO input should produce a concise CLI error and exit code one."""
    po_path = tmp_path / "locales" / "zh_CN" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True)
    po_path.write_text('msgid "unterminated\n', encoding="utf-8")

    exit_code = upsert_i18n_module.main(
        ["--po-file", str(po_path), "--pair", "New message", "新消息"]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Failed to update API translations" in captured.err
