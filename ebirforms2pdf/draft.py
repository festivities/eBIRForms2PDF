"""Parse eBIRForms pseudo-XML drafts into control-id values. Values are never logged."""

import re
from dataclasses import dataclass
from pathlib import Path

from .finder import parse_filename

_DIV_RE = re.compile(r"<div>(.*?)</div>", re.DOTALL)
_UNICODE_ESCAPE_RE = re.compile(r"%u([0-9A-Fa-f]{4})")
_BYTE_ESCAPE_RE = re.compile(r"%([0-9A-Fa-f]{2})")


@dataclass
class DraftMeta:
    form_code: str
    period: str
    tin: str
    max_page: int | None


def js_unescape(text):
    """Unescape JS escape() output: %uXXXX and %XX; '+' stays literal."""
    text = _UNICODE_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)
    return _BYTE_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)


def _split_line(line):
    eq = line.find("=")
    if eq < 0:
        return None
    control_id = line[:eq].strip()
    if not control_id:
        return None
    rest = line[eq + 1 :]
    terminator = control_id + "="
    if rest.endswith(terminator):
        value = rest[: -len(terminator)].rstrip()
    else:
        value = rest.strip()
    return control_id, value


def _find_max_page(values):
    for key in values:
        if key.endswith(":txtMaxPage"):
            try:
                return int(values[key])
            except (TypeError, ValueError):
                return None
    return None


def parse_draft(path):
    """Return (DraftMeta, values dict) for a draft file."""
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    values = {}
    for match in _DIV_RE.finditer(raw):
        line = match.group(1).strip()
        if not line:
            continue
        split = _split_line(line)
        if split is None:
            continue
        control_id, value = split
        value = js_unescape(value)
        if control_id in values:
            values[control_id] += "\n" + value
        else:
            values[control_id] = value
    parsed = parse_filename(Path(path).name)
    stem = Path(path).name
    if stem.lower().endswith(".xml"):
        stem = stem[:-4]
    tin = stem.split("-", 1)[0] if stem.split("-", 1)[0].isdigit() else ""
    meta = DraftMeta(
        form_code=parsed[1] if parsed else "",
        period=parsed[2] if parsed else "",
        tin=tin,
        max_page=_find_max_page(values),
    )
    return meta, values
