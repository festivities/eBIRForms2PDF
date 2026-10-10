"""Command line interface for eBIRForms2PDF."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .extract import ExtractError, extract_templates
from .finder import FormEntry, looks_like_draft, parse_filename, scan
from .locator import find_install_root
from .render import export_pdf, output_pdf_name


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ebirforms2pdf", description="Export eBIRForms drafts as fitted A4 PDFs."
    )
    parser.add_argument("drafts", nargs="*", help="explicit draft .xml file paths")
    parser.add_argument("--list", action="store_true", help="list saved drafts and exit")
    parser.add_argument("--all", action="store_true", help="export all found drafts")
    parser.add_argument("--out", metavar="DIR", help="output directory (default: prompt)")
    parser.add_argument(
        "--paper",
        choices=("a4", "legal"),
        default=None,
        help="output paper size: a4 or Philippine legal 8.5x13in (default: a4)",
    )
    parser.add_argument("--root", metavar="PATH", help="eBIRForms install folder")
    parser.add_argument("--cache", metavar="DIR", help="template cache directory")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    return parser.parse_args(argv)


def _format_size(size):
    value = float(size)
    for unit in ("B", "KB", "MB"):
        if value < 1024 or unit == "MB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} MB"


def _format_time(mtime):
    import time

    return time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))


def _print_table(entries):
    print(f"{'#':>3}  {'form code':<14} {'period':<10} {'size':>10}  {'modified':<16}  file")
    for index, entry in enumerate(entries, start=1):
        marker = "  [encrypted - not exportable]" if entry.encrypted else ""
        print(
            f"{index:>3}  {entry.form_code or '?':<14} {entry.period or '?':<10}"
            f" {_format_size(entry.size):>10}  {_format_time(entry.mtime):<16}"
            f"  {entry.filename}{marker}"
        )


def _parse_selection(text, count):
    stripped = text.strip().lower()
    if stripped in ("all", "a"):
        return list(range(count))
    picked = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, _, high = part.partition("-")
            if low.strip().isdigit() and high.strip().isdigit():
                for i in range(int(low), int(high) + 1):
                    if 1 <= i <= count:
                        picked.add(i - 1)
        elif part.isdigit() and 1 <= int(part) <= count:
            picked.add(int(part) - 1)
    return sorted(picked)


def _entry_from_path(path):
    stat = path.stat()
    parsed = parse_filename(path.name)
    return FormEntry(
        path=path,
        form_code=parsed[1] if parsed else "",
        period=parsed[2] if parsed else "",
        encrypted=False,
        size=stat.st_size,
        mtime=stat.st_mtime,
        filename=path.name,
    )


def _prompt(message, default):
    try:
        answer = input(f"{message} [{default}]: ").strip()
    except EOFError:
        return default
    if len(answer) >= 2 and answer[0] == answer[-1] and answer[0] in "\"'":
        answer = answer[1:-1]
    return answer or default


def _do_exports(entries, out_dir, named_dir, paper):
    successes = 0
    for entry in entries:
        target = out_dir / output_pdf_name(entry.filename, paper)
        if entry.encrypted:
            print(f"SKIP {entry.filename}: not exportable (encrypted final copy)")
            continue
        try:
            result = export_pdf(entry, entry.path, named_dir, target, paper)
        except Exception as exc:
            print(f"ERROR {entry.filename}: {exc}")
            continue
        pages = result.pages if result.pages > 0 else "?"
        print(
            f"OK {entry.filename} -> {target} ({result.paper}, {pages} pages,"
            f" scale {result.scale:.3f})"
        )
        successes += 1
    return successes


def main(argv=None):
    args = _parse_args(argv)
    if args.version:
        print(f"ebirforms2pdf {__version__}")
        return 0
    root = find_install_root(args.root)
    if root is None:
        if args.root:
            print(f"'{args.root}' does not look like an eBIRForms install")
            print("(it must contain BIRForms.exe and a savefile folder)")
        else:
            print("eBIRForms installation not found (checked registry and default paths)")
        print("Pass --root PATH pointing at the eBIRForms install folder")
        return 1
    print(f"install: {root}")
    if args.drafts:
        entries = []
        for raw in args.drafts:
            path = Path(raw)
            if not path.is_file():
                print(f"ERROR: draft file not found: {path}")
                return 1
            entry = _entry_from_path(path)
            if not entry.encrypted and not looks_like_draft(path):
                print(f"ERROR: not an eBIRForms draft: {path}")
                return 1
            entries.append(entry)
    else:
        entries = scan(root)
    if args.list:
        if entries:
            _print_table(entries)
        else:
            print("no saved drafts found")
        return 0
    if not entries:
        print("no saved drafts found; nothing to export")
        return 0
    try:
        named_dir = extract_templates(root / "BIRForms.exe", args.cache)
    except ExtractError as exc:
        print(f"ERROR: template extraction failed: {exc}")
        return 1
    print(f"templates: {named_dir}")
    interactive = not args.all and not args.drafts
    if interactive:
        _print_table(entries)
        selection = _prompt("Select forms (e.g. 1,3-5 or all)", "all")
        chosen = _parse_selection(selection, len(entries))
        if not chosen:
            print("nothing selected")
            return 1
        entries = [entries[i] for i in chosen]
    if args.paper:
        paper = args.paper
    elif interactive:
        paper = _prompt("Paper size (a4/legal)", "a4").strip().lower()
        if paper not in ("a4", "legal"):
            print(f"unknown paper size '{paper}', using a4")
            paper = "a4"
    else:
        paper = "a4"
    if args.out:
        out_dir = Path(args.out)
    elif interactive:
        out_dir = Path(_prompt("Output directory", str(Path.cwd())))
    else:
        out_dir = Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    successes = _do_exports(entries, out_dir, named_dir, paper)
    if successes > 0:
        return 0
    print("no exports succeeded")
    return 1


if __name__ == "__main__":
    sys.exit(main())
