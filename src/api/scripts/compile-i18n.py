"""Compile API gettext PO catalogs into runtime MO files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from i18n_catalog import read_catalog, write_mo_catalog


def compile_catalog(po_path: Path, mo_path: Path, use_fuzzy: bool) -> None:
    """Compile one PO file into an MO file.

    Args:
        po_path: Source PO catalog path.
        mo_path: Destination MO catalog path.
        use_fuzzy: Whether fuzzy translations should be included.

    Returns:
        None.

    Raises:
        OSError: If the catalog files cannot be read or written.
        PoFileError: If Babel cannot parse the PO catalog.
        ValueError: If Babel cannot compile the catalog.
    """
    catalog = read_catalog(po_path)
    write_mo_catalog(mo_path, catalog, use_fuzzy=use_fuzzy)


def find_po_files(locale_root: Path, locale: str | None, domain: str) -> list[Path]:
    """Find PO files filtered by locale and translation domain.

    Args:
        locale_root: Root directory containing locale subdirectories.
        locale: Optional locale name such as ``zh_CN``.
        domain: Translation domain such as ``messages``.

    Returns:
        Sorted PO paths that exist under the locale root.

    Raises:
        OSError: If filesystem path resolution fails.
    """
    if locale:
        po_path = locale_root / locale / "LC_MESSAGES" / f"{domain}.po"
        return [po_path] if po_path.exists() else []

    return sorted(locale_root.glob(f"*/LC_MESSAGES/{domain}.po"))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the standalone catalog compiler.

    Returns:
        Parsed CLI namespace.

    Raises:
        SystemExit: If argparse rejects the CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description="Compile gettext .po files to .mo files."
    )
    parser.add_argument(
        "--locale",
        help="Only compile the specified locale, for example zh_CN.",
    )
    parser.add_argument(
        "--domain",
        default="messages",
        help="Translation domain name. Default: messages.",
    )
    parser.add_argument(
        "--locale-dir",
        default=None,
        help="Locale root directory. Default: <project>/app/locales.",
    )
    parser.add_argument(
        "--use-fuzzy",
        action="store_true",
        help="Include fuzzy translations when compiling.",
    )
    return parser.parse_args()


def main() -> int:
    """Compile selected API gettext catalogs.

    Returns:
        Process exit code: zero on success and one when no PO files are found.

    Raises:
        OSError: If catalog files cannot be read or written.
        PoFileError: If Babel cannot parse a PO catalog.
        ValueError: If Babel cannot compile a catalog.
    """
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    locale_root = (
        Path(args.locale_dir).resolve()
        if args.locale_dir
        else project_root / "app" / "locales"
    )

    po_files = find_po_files(locale_root, args.locale, args.domain)
    if not po_files:
        target = (
            f"{args.locale}/{args.domain}.po"
            if args.locale
            else f"*/LC_MESSAGES/{args.domain}.po"
        )
        print(f"No PO files found: {target}", file=sys.stderr)
        return 1

    for po_path in po_files:
        mo_path = po_path.with_suffix(".mo")
        compile_catalog(po_path, mo_path, args.use_fuzzy)
        print(
            f"Compiled {po_path.relative_to(project_root)} -> {mo_path.relative_to(project_root)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
