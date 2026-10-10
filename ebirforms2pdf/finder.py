"""Scan an eBIRForms install for saved drafts and encrypted final copies."""

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path

DRAFT_DIRS = ("savefile", "temp")
ENCRYPTED_DIR_SUFFIXES = ("_Copy", "_Archive")
UTF8_BOM = b"\xef\xbb\xbf"


@dataclass
class FormEntry:
    path: Path
    form_code: str
    period: str
    encrypted: bool
    size: int
    mtime: float
    filename: str


def parse_filename(filename):
    """Split 'TIN-formCode-period.xml' into (tin, form_code, period)."""
    stem = filename
    if stem.lower().endswith(".xml"):
        stem = stem[:-4]
    if "#" in stem:
        stem = stem.split("#", 1)[0]
    parts = stem.split("-")
    if len(parts) < 3:
        return None
    tin, form_code, period = parts[0], parts[1], "-".join(parts[2:])
    if not tin.isascii() or not tin.isdecimal() or not 9 <= len(tin) <= 14:
        return None
    if not form_code or not period:
        return None
    return tin, form_code, period


def looks_like_draft(path):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return False
    raw = raw.removeprefix(UTF8_BOM)
    if not raw.startswith(b"<?xml"):
        return False
    text = raw.decode("utf-8", errors="replace")
    return "<div>frm" in text and "txtFinalFlag=" in text


def looks_encrypted(path):
    """True for a non-empty file without the plain XML header (an encrypted final copy)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(512).removeprefix(UTF8_BOM)
    except OSError:
        return False
    return bool(head) and not head.startswith(b"<?xml")


def _make_entry(path, encrypted):
    try:
        stat = path.stat()
    except OSError:
        return None
    parsed = parse_filename(path.name)
    return FormEntry(
        path=path,
        form_code=parsed[1] if parsed else "",
        period=parsed[2] if parsed else "",
        encrypted=encrypted,
        size=stat.st_size,
        mtime=stat.st_mtime,
        filename=path.name,
    )


def _scan_plain_dir(directory):
    entries = []
    try:
        it = os.scandir(directory)
    except OSError:
        return entries
    with it:
        for item in it:
            if not item.name.lower().endswith(".xml") or not item.is_file():
                continue
            path = Path(item.path)
            if looks_like_draft(path):
                entry = _make_entry(path, False)
                if entry is not None:
                    entries.append(entry)
    return entries


def _scan_encrypted_dirs(root):
    entries = []
    try:
        it = os.scandir(root)
    except OSError:
        return entries
    with it:
        for item in it:
            if not item.is_dir() or not item.name.startswith("IAF_"):
                continue
            if not item.name.endswith(ENCRYPTED_DIR_SUFFIXES):
                continue
            for path in sorted(Path(item.path).glob("*.xml")):
                if not fnmatch.fnmatch(path.name, "*#*#*.xml"):
                    continue
                encrypted = looks_encrypted(path)
                if not encrypted and not looks_like_draft(path):
                    continue
                entry = _make_entry(path, encrypted)
                if entry is not None:
                    entries.append(entry)
    return entries


def scan(root):
    """Return FormEntry list for drafts and encrypted copies under root."""
    root = Path(root)
    entries = []
    for sub in DRAFT_DIRS:
        entries.extend(_scan_plain_dir(root / sub))
    entries.extend(_scan_encrypted_dirs(root))
    entries.sort(key=lambda e: e.path.name.lower())
    return entries
