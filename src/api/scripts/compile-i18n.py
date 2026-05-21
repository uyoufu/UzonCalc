from __future__ import annotations

import argparse
import sys
from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po


def compile_catalog(po_path: Path, mo_path: Path, use_fuzzy: bool) -> None:
    """编译单个 .po 文件为 .mo 文件。"""
    with po_path.open("r", encoding="utf-8") as po_file:
        catalog = read_po(po_file, locale=po_path.parent.parent.name)

    mo_path.parent.mkdir(parents=True, exist_ok=True)
    with mo_path.open("wb") as mo_file:
        write_mo(mo_file, catalog, use_fuzzy=use_fuzzy)


def find_po_files(locale_root: Path, locale: str | None, domain: str) -> list[Path]:
    """按语言和 domain 过滤待编译的 .po 文件。"""
    if locale:
        po_path = locale_root / locale / "LC_MESSAGES" / f"{domain}.po"
        return [po_path] if po_path.exists() else []

    return sorted(locale_root.glob(f"*/LC_MESSAGES/{domain}.po"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile gettext .po files to .mo files.")
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
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    locale_root = Path(args.locale_dir).resolve() if args.locale_dir else project_root / "app" / "locales"

    po_files = find_po_files(locale_root, args.locale, args.domain)
    if not po_files:
        target = f"{args.locale}/{args.domain}.po" if args.locale else f"*/LC_MESSAGES/{args.domain}.po"
        print(f"No PO files found: {target}", file=sys.stderr)
        return 1

    for po_path in po_files:
        mo_path = po_path.with_suffix(".mo")
        compile_catalog(po_path, mo_path, args.use_fuzzy)
        print(f"Compiled {po_path.relative_to(project_root)} -> {mo_path.relative_to(project_root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())