"""Command line interface for eBIRForms2PDF."""

import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .extract import ExtractError, extract_templates
from .finder import FormEntry, looks_encrypted, looks_like_draft, parse_filename, scan
from .locator import find_install_root
from .render import export_many


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


def _number(text):
    if text.isascii() and text.isdecimal() and len(text) <= 9:
        return int(text)
    return None


def _parse_selection(text, count):
    """Return (sorted zero-based indexes, invalid tokens); 'all' or 'a' selects everything."""
    if text.strip().lower() in ("all", "a"):
        return list(range(count)), []
    picked, invalid = set(), []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        low_text, dash, high_text = token.partition("-")
        low = _number(low_text.strip())
        high = _number(high_text.strip()) if dash else low
        if low is None or high is None or min(low, high) < 1 or max(low, high) > count:
            invalid.append(token)
            continue
        picked.update(range(min(low, high) - 1, max(low, high)))
    return sorted(picked), invalid


def _entry_from_path(path):
    stat = path.stat()
    parsed = parse_filename(path.name)
    return FormEntry(
        path=path,
        form_code=parsed[1] if parsed else "",
        period=parsed[2] if parsed else "",
        encrypted=looks_encrypted(path),
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


def _pick(entries):
    """Ask for forms (3 tries). Returns the chosen entries, or None when cancelled or invalid."""
    for _ in range(3):
        try:
            answer = input("Select forms (e.g. 1,3-5 or all) [all]: ").strip() or "all"
        except EOFError:
            print("cancelled")
            return None
        chosen, invalid = _parse_selection(answer, len(entries))
        if not invalid:
            if not chosen:
                print("nothing selected")
                return None
            return [entries[i] for i in chosen]
        print(f"invalid selection: {', '.join(invalid)} (use 1-{len(entries)}, ranges, or all)")
    print("too many invalid selections")
    return None


def _do_exports(entries, out_dir, named_dir, paper):
    """Print each export result. Returns (succeeded, failed) counts; skips are neither."""
    succeeded = failed = 0
    for status, line in export_many(entries, out_dir, named_dir, paper):
        print(line)
        if status == "OK":
            succeeded += 1
        elif status == "ERROR":
            failed += 1
    return succeeded, failed


def _main(argv):
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
    failed = 0
    if args.drafts:
        if args.all:
            print("note: --all is ignored when draft paths are given")
        entries = []
        for raw in args.drafts:
            path = Path(raw)
            if not path.is_file():
                print(f"ERROR {path}: file not found")
                failed += 1
            elif not looks_encrypted(path) and not looks_like_draft(path):
                print(f"ERROR {path}: not an eBIRForms draft")
                failed += 1
            else:
                entries.append(_entry_from_path(path))
    else:
        entries = scan(root)
    if args.list:
        if entries:
            _print_table(entries)
        else:
            print("no saved drafts found")
        return 1 if failed else 0
    if not entries:
        print("no saved drafts found; nothing to export")
        return 1 if failed else 0
    try:
        named_dir = extract_templates(root / "BIRForms.exe", args.cache)
    except ExtractError as exc:
        print(f"ERROR: template extraction failed: {exc}")
        return 1
    print(f"templates: {named_dir}")
    interactive = not args.all and not args.drafts
    if interactive:
        _print_table(entries)
        picked = _pick(entries)
        if picked is None:
            return 1
        entries = picked
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
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: cannot create output folder {out_dir}: {exc}")
        return 1
    succeeded, export_failures = _do_exports(entries, out_dir, named_dir, paper)
    failed += export_failures
    if succeeded == 0:
        print("no exports succeeded")
        return 1
    if failed:
        print(f"{failed} failed, {succeeded} exported")
        return 2
    return 0


def main(argv=None):
    try:
        return _main(argv)
    except KeyboardInterrupt:
        print("\ncancelled")
        return 130


if __name__ == "__main__":
    sys.exit(main())
