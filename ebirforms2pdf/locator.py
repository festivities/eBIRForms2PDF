"""Locate the eBIRForms offline installation."""

import os
import winreg
from pathlib import Path

_UNINSTALL_KEY = (
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\eBIRForms_is1"
)


def _registry_candidates():
    paths = [
        (_UNINSTALL_KEY, winreg.KEY_WOW64_64KEY),
        (_UNINSTALL_KEY, winreg.KEY_WOW64_32KEY),
        (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\eBIRForms_is1",
            winreg.KEY_WOW64_32KEY,
        ),
        (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\eBIRForms_is1",
            winreg.KEY_WOW64_64KEY,
        ),
    ]
    for key_path, view in paths:
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | view
            ) as key:
                location, _ = winreg.QueryValueEx(key, "InstallLocation")
                if location:
                    yield Path(location)
        except OSError:
            continue


def is_install_root(path):
    path = Path(path)
    return (path / "BIRForms.exe").is_file() and (path / "savefile").is_dir()


def find_install_root(override=None):
    """Return the eBIRForms install dir, or None if not found."""
    if override:
        return Path(override) if is_install_root(override) else None
    for candidate in _registry_candidates():
        if is_install_root(candidate):
            return candidate
    home = os.environ.get("USERPROFILE")
    fallbacks = [
        Path(r"C:\Apps\eBIRForms"),
        Path(r"C:\eBIRForms"),
        Path(home) / "eBIRForms" if home else None,
    ]
    for candidate in fallbacks:
        if candidate and is_install_root(candidate):
            return candidate
    return None
