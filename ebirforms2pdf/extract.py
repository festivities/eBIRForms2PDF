"""Extract the embedded web bundle (form templates) from BIRForms.exe."""

import os
from pathlib import Path, PureWindowsPath

import pefile

RT_HTML = 23
MANIFEST_ID = 129
XOR_TABLE = bytes(i ^ 0xFF for i in range(256))
COMPLETE_MARKER = ".complete"


class ExtractError(Exception):
    pass


def default_cache_base():
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "eBIRForms2PDF" / "cache"
    return Path.home() / ".ebirforms2pdf" / "cache"


def _collect_resources(pe):
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
    )
    if not hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        raise ExtractError("BIRForms.exe has no resource directory")
    for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if not entry.struct or entry.struct.Id != RT_HTML:
            continue
        resources = {}
        for id_entry in entry.directory.entries:
            if not id_entry.struct or not id_entry.struct.Id:
                continue
            if not hasattr(id_entry, "directory"):
                continue
            for lang_entry in id_entry.directory.entries:
                data = getattr(lang_entry, "data", None)
                if data and data.struct:
                    resources[id_entry.struct.Id] = (
                        data.struct.OffsetToData,
                        data.struct.Size,
                    )
        return resources
    raise ExtractError("no RT_HTML resources found in BIRForms.exe")


def _safe_dest(named_dir, rel_path):
    pure = PureWindowsPath(rel_path.strip())
    if pure.anchor or ".." in pure.parts or not pure.parts:
        return None
    return named_dir.joinpath(*pure.parts)


def extract_templates(exe_path, cache_base=None):
    """Decode all RT_HTML resources into cache_base/<key>/named and return that dir."""
    try:
        return _extract_templates(Path(exe_path), cache_base)
    except (pefile.PEFormatError, UnicodeDecodeError, OSError) as exc:
        raise ExtractError(f"could not extract templates: {exc}") from exc


def _extract_templates(exe, cache_base):
    if not exe.is_file():
        raise ExtractError(f"BIRForms.exe not found: {exe}")
    base = Path(cache_base) if cache_base else default_cache_base()
    stat = exe.stat()
    named_dir = base / f"{stat.st_size}-{int(stat.st_mtime)}" / "named"
    marker = named_dir / COMPLETE_MARKER
    if marker.is_file():
        return named_dir
    pe = pefile.PE(str(exe), fast_load=True)
    try:
        resources = _collect_resources(pe)
        if MANIFEST_ID not in resources:
            raise ExtractError(
                "manifest resource 129 is missing; the app layout changed"
            )
        manifest = pe.get_data(*resources[MANIFEST_ID])
        manifest_text = manifest.decode("utf-16-le", errors="strict").lstrip("\ufeff")
        for index, rel_path in enumerate(manifest_text.split("|")[1:], start=1):
            resource_id = MANIFEST_ID + index
            if resource_id not in resources:
                continue
            dest = _safe_dest(named_dir, rel_path)
            if dest is None:
                continue
            payload = pe.get_data(*resources[resource_id])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload.translate(XOR_TABLE))
    finally:
        pe.close()
    if not (named_dir / "BIRForms.hta").is_file():
        raise ExtractError("template extraction produced no BIRForms.hta")
    marker.touch()
    return named_dir
