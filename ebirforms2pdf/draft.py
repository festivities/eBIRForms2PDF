"""Parse eBIRForms pseudo-XML drafts into control-id values. Values are never logged."""

import re
from dataclasses import dataclass
from pathlib import Path

_DIV_RE = re.compile(r"<div>(.*?)</div>", re.DOTALL)
_ESCAPE_RE = re.compile(r"%u([0-9A-Fa-f]{4})|%([0-9A-Fa-f]{2})")


@dataclass
class DraftMeta:
    max_page: int | None


def js_unescape(text):
    """Unescape JS escape() output in one pass (%uXXXX, %XX); '+' stays literal."""
    text = _ESCAPE_RE.sub(lambda m: chr(int(m.group(1) or m.group(2), 16)), text)
    return text.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "surrogatepass")


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
    return DraftMeta(max_page=_find_max_page(values)), values
