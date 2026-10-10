"""Scan an eBIRForms install for saved drafts and encrypted final copies."""

import fnmatch
import math
import os
from dataclasses import dataclass
from pathlib import Path

DRAFT_DIRS = ("savefile", "temp")
ENCRYPTED_DIR_SUFFIXES = ("_Copy", "_Archive")
ENTROPY_THRESHOLD = 6.0


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
    if not tin.isdigit() or not 9 <= len(tin) <= 14 or not form_code or not period:
        return None
    return tin, form_code, period


def looks_like_draft(path):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return False
    if not raw.startswith(b"<?xml"):
        return False
    text = raw.decode("utf-8", errors="replace")
    return "<div>frm" in text and "txtFinalFlag=" in text


def shannon_entropy(data):
    if not data:
        return 0.0
    counts = {}
    for byte in data:
        counts[byte] = counts.get(byte, 0) + 1
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _looks_encrypted(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(512)
    except OSError:
        return False
    if head.startswith(b"<?xml"):
        return False
    return shannon_entropy(head) > ENTROPY_THRESHOLD


def _plain_entry(path):
    parsed = parse_filename(path.name)
    form_code = parsed[1] if parsed else ""
    period = parsed[2] if parsed else ""
    stat = path.stat()
    return FormEntry(
        path=path,
        form_code=form_code,
        period=period,
        encrypted=False,
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
                entries.append(_plain_entry(path))
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
                if path.stat().st_size == 0:
                    continue
                encrypted = _looks_encrypted(path)
                parsed = parse_filename(path.name)
                stat = path.stat()
                entries.append(
                    FormEntry(
                        path=path,
                        form_code=parsed[1] if parsed else "",
                        period=parsed[2] if parsed else "",
                        encrypted=encrypted,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        filename=path.name,
                    )
                )
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
