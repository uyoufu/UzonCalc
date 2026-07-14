"""Add, update, or delete API gettext translations and compile the MO file."""

from __future__ import annotations

import argparse
import os
import stat
import sys
import tempfile
from pathlib import Path
from string import Formatter
from typing import Sequence

from babel.messages.catalog import Catalog
from babel.messages.pofile import PoFileError

from i18n_catalog import read_catalog, write_mo_catalog, write_po_catalog

DEFAULT_PO_PATH = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "locales"
    / "zh_CN"
    / "LC_MESSAGES"
    / "messages.po"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for catalog updates or deletions.

    Args:
        argv: Arguments after the script name. ``None`` reads from ``sys.argv``.

    Returns:
        Parsed CLI namespace.

    Raises:
        SystemExit: If arguments are invalid or update/delete modes are mixed.
    """
    parser = argparse.ArgumentParser(
        description="Add, update, or delete API gettext translations and compile the MO file."
    )
    parser.add_argument(
        "--po-file",
        type=Path,
        default=DEFAULT_PO_PATH,
        help="PO catalog path. Default: app/locales/zh_CN/LC_MESSAGES/messages.po.",
    )

    operation_group = parser.add_mutually_exclusive_group(required=True)
    operation_group.add_argument(
        "--pair",
        action="append",
        default=[],
        nargs=2,
        metavar=("MSGID", "MSGSTR"),
        help="Add or update one English msgid and Chinese msgstr. May be repeated.",
    )
    operation_group.add_argument(
        "--delete",
        action="append",
        default=[],
        dest="delete_message_ids",
        metavar="MSGID",
        help="Delete one msgid. Missing entries are ignored. May be repeated.",
    )
    return parser.parse_args(argv)


def get_placeholder_names(message: str) -> frozenset[str]:
    """Extract Python format placeholder names from a message.

    Args:
        message: Gettext message text that may contain ``str.format`` fields.

    Returns:
        Placeholder names used by the message.

    Raises:
        ValueError: If the message contains malformed format braces.
    """
    try:
        placeholder_names = {
            field_name
            for _, field_name, _, _ in Formatter().parse(message)
            if field_name is not None
        }
    except ValueError as error:
        raise ValueError(
            f"Invalid format placeholder in message {message!r}: {error}"
        ) from error

    return frozenset(placeholder_names)


def validate_update_pairs(pairs: Sequence[tuple[str, str]]) -> None:
    """Validate translation values and placeholder compatibility.

    Args:
        pairs: English msgid and Chinese msgstr pairs.

    Returns:
        None.

    Raises:
        ValueError: If a value is blank, has malformed placeholders, or uses a
            different placeholder set from its counterpart.
    """
    for message_id, translation in pairs:
        if not message_id.strip() or not translation.strip():
            raise ValueError("Message IDs and translations cannot be blank.")

        message_placeholders = get_placeholder_names(message_id)
        translation_placeholders = get_placeholder_names(translation)
        if message_placeholders != translation_placeholders:
            raise ValueError(
                "Translation placeholder names must match the msgid: "
                f"{message_id!r} uses {sorted(message_placeholders)}, "
                f"but msgstr uses {sorted(translation_placeholders)}."
            )


def validate_delete_message_ids(message_ids: Sequence[str]) -> None:
    """Validate gettext message identifiers requested for deletion.

    Args:
        message_ids: Message identifiers to delete.

    Returns:
        None.

    Raises:
        ValueError: If any message identifier is blank.
    """
    if any(not message_id.strip() for message_id in message_ids):
        raise ValueError("Message IDs cannot be blank.")


def apply_catalog_changes(
    catalog: Catalog,
    *,
    pairs: Sequence[tuple[str, str]],
    delete_message_ids: Sequence[str],
) -> bool:
    """Apply one validated operation mode to an in-memory catalog.

    Args:
        catalog: Catalog to mutate.
        pairs: English msgid and Chinese msgstr pairs.
        delete_message_ids: Message identifiers to delete.

    Returns:
        Whether the catalog content changed.

    Raises:
        ValueError: If both modes are supplied, neither mode is supplied, input
            validation fails, or a targeted entry is plural.
    """
    if bool(pairs) == bool(delete_message_ids):
        raise ValueError("Provide either translation pairs or message IDs to delete.")

    if pairs:
        validate_update_pairs(pairs)
        targeted_messages = [catalog.get(message_id) for message_id, _ in pairs]
    else:
        validate_delete_message_ids(delete_message_ids)
        targeted_messages = [
            catalog.get(message_id) for message_id in delete_message_ids
        ]

    plural_message_ids = [
        message.id
        for message in targeted_messages
        if message is not None and isinstance(message.id, tuple)
    ]
    if plural_message_ids:
        raise ValueError(
            f"Plural gettext entries are not supported: {plural_message_ids!r}"
        )

    has_changes = False
    if pairs:
        for message_id, translation in pairs:
            message = catalog.get(message_id)
            if message is None:
                catalog.add(message_id, translation)
                has_changes = True
            elif message.string != translation:
                message.string = translation
                has_changes = True
        return has_changes

    for message_id in delete_message_ids:
        if catalog.get(message_id) is None:
            continue
        del catalog[message_id]
        has_changes = True
    return has_changes


def create_temporary_catalog_path(target_path: Path) -> Path:
    """Create an empty temporary file beside a target catalog file.

    Args:
        target_path: Final catalog path used to choose the directory and prefix.

    Returns:
        Path to the temporary file.

    Raises:
        OSError: If the temporary file cannot be created.
    """
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=target_path.parent,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    )
    os.close(file_descriptor)
    return Path(temporary_name)


def apply_target_permissions(temporary_path: Path, target_path: Path) -> None:
    """Apply stable file permissions before atomically replacing a catalog.

    Args:
        temporary_path: Newly serialized temporary file.
        target_path: Existing or planned final file.

    Returns:
        None.

    Raises:
        OSError: If file metadata cannot be read or changed.
    """
    target_mode = (
        stat.S_IMODE(target_path.stat().st_mode) if target_path.exists() else 0o644
    )
    temporary_path.chmod(target_mode)


def write_catalog_files(po_path: Path, catalog: Catalog) -> Path:
    """Serialize and atomically replace the PO and compiled MO catalogs.

    Both temporary files are fully generated before either destination is
    replaced. The MO file is replaced first so a failed PO replacement can be
    repaired by safely rerunning the same update command.

    Args:
        po_path: Final PO catalog path.
        catalog: Updated catalog to serialize and compile.

    Returns:
        Path to the compiled MO file.

    Raises:
        OSError: If temporary or destination files cannot be written.
        ValueError: If Babel cannot serialize or compile the catalog.
    """
    mo_path = po_path.with_suffix(".mo")
    temporary_po_path = create_temporary_catalog_path(po_path)
    temporary_mo_path = create_temporary_catalog_path(mo_path)

    try:
        write_po_catalog(temporary_po_path, catalog)
        write_mo_catalog(temporary_mo_path, catalog)
        apply_target_permissions(temporary_po_path, po_path)
        apply_target_permissions(temporary_mo_path, mo_path)
        temporary_mo_path.replace(mo_path)
        temporary_po_path.replace(po_path)
    finally:
        temporary_po_path.unlink(missing_ok=True)
        temporary_mo_path.unlink(missing_ok=True)

    return mo_path


def update_catalog(
    *,
    po_path: Path,
    pairs: Sequence[tuple[str, str]],
    delete_message_ids: Sequence[str],
) -> bool:
    """Update one PO catalog and automatically compile its MO file.

    Args:
        po_path: PO catalog to update.
        pairs: English msgid and Chinese msgstr pairs.
        delete_message_ids: Message identifiers to delete.

    Returns:
        Whether either operation changed the catalog.

    Raises:
        OSError: If catalog files cannot be read or written.
        ValueError: If inputs or catalog content are invalid.
    """
    catalog = read_catalog(po_path)
    has_changes = apply_catalog_changes(
        catalog,
        pairs=pairs,
        delete_message_ids=delete_message_ids,
    )
    if not has_changes:
        return False

    write_catalog_files(po_path, catalog)
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Run the gettext catalog update command.

    Args:
        argv: Arguments after the script name. ``None`` reads from ``sys.argv``.

    Returns:
        Process exit code: zero on success and one on catalog failures.

    Raises:
        SystemExit: If argparse rejects the CLI arguments.
    """
    args = parse_args(argv)
    po_path = args.po_file.resolve()
    pairs = [tuple(pair) for pair in args.pair]

    try:
        has_changes = update_catalog(
            po_path=po_path,
            pairs=pairs,
            delete_message_ids=args.delete_message_ids,
        )
    except (OSError, PoFileError, ValueError) as error:
        print(f"Failed to update API translations: {error}", file=sys.stderr)
        return 1

    if not has_changes:
        print(f"No translation changes: {po_path}")
        return 0

    print(f"Updated PO catalog: {po_path}")
    print(f"Compiled MO catalog: {po_path.with_suffix('.mo')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
