"""Validate the extension manifest and version single-sourcing."""

import re
from pathlib import Path

from core import __version__

MANIFEST = Path(__file__).resolve().parents[2] / "magnets" / "blender_manifest.toml"


def _load_manifest() -> dict:
    text = MANIFEST.read_text(encoding="utf-8")
    try:
        import tomllib

        return tomllib.loads(text)
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        data = {}
        for key in ("id", "version", "type", "blender_version_min"):
            m = re.search(rf'^\s*{key}\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if m:
                data[key] = m.group(1)
        return data


def test_manifest_exists():
    assert MANIFEST.is_file()


def test_required_fields():
    data = _load_manifest()
    assert data["id"] == "magnets"
    assert data["type"] == "add-on"
    assert data["blender_version_min"] == "4.2.0"


def test_version_matches_core():
    data = _load_manifest()
    assert data["version"] == __version__, (
        "blender_manifest.toml version must match magnets/core/__init__.py"
    )
