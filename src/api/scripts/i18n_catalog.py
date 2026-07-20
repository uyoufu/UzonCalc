"""Shared Babel helpers for reading, writing, and compiling gettext catalogs."""

from __future__ import annotations

import io
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po


def read_catalog(po_path: Path) -> Catalog:
    """Read a gettext PO file into a Babel catalog.

    Args:
        po_path: Path to the PO file. Its locale is inferred from the standard
            ``<locale>/LC_MESSAGES/<domain>.po`` directory layout.

    Returns:
        Parsed Babel catalog.

    Raises:
        OSError: If the PO file cannot be opened.
        PoFileError: If Babel cannot parse the PO file.
    """
    locale = po_path.parent.parent.name
    with po_path.open("r", encoding="utf-8") as po_file:
        return read_po(po_file, locale=locale, abort_invalid=True)


def write_po_catalog(po_path: Path, catalog: Catalog) -> None:
    """Serialize a Babel catalog as a UTF-8 PO file.

    Args:
        po_path: Destination PO file path.
        catalog: Catalog to serialize.

    Returns:
        None.

    Raises:
        OSError: If the destination cannot be created or written.
        ValueError: If the catalog contains invalid PO content.
    """
    po_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    write_po(buffer, catalog)
    # Babel terminates the final entry with a blank separator line. Keeping one
    # terminal newline avoids repository whitespace warnings without changing PO syntax.
    po_path.write_bytes(buffer.getvalue().rstrip(b"\n") + b"\n")


def write_mo_catalog(
    mo_path: Path,
    catalog: Catalog,
    *,
    use_fuzzy: bool = False,
) -> None:
    """Compile a Babel catalog into a gettext MO file.

    Args:
        mo_path: Destination MO file path.
        catalog: Catalog to compile.
        use_fuzzy: Whether fuzzy translations should be included.

    Returns:
        None.

    Raises:
        OSError: If the destination cannot be created or written.
        ValueError: If the catalog cannot be compiled.
    """
    mo_path.parent.mkdir(parents=True, exist_ok=True)
    with mo_path.open("wb") as mo_file:
        write_mo(mo_file, catalog, use_fuzzy=use_fuzzy)
