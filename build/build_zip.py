#!/usr/bin/env python3
"""Package the ``magnets/`` extension into a distributable zip.

For Blender 4.2+ Extensions the ``blender_manifest.toml`` must sit at the root
of the zip, so this script zips the *contents* of ``magnets/`` at the archive
root. Output: ``dist/magnets-<version>.zip``.

Usage:
    python build/build_zip.py

The official alternative is ``blender --command extension build``; this script
keeps CI dependency-free (no Blender binary required to package).
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = REPO_ROOT / "magnets"
MANIFEST = PKG_DIR / "blender_manifest.toml"
DIST_DIR = REPO_ROOT / "dist"
LICENSE_FILE = REPO_ROOT / "LICENSE"

# Files/dirs never shipped in the extension.
EXCLUDE_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def read_version() -> str:
    text = MANIFEST.read_text(encoding="utf-8")
    try:
        import tomllib  # Python 3.11+ (Blender 4.2 bundles 3.11)

        return tomllib.loads(text)["version"]
    except ModuleNotFoundError:
        match = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if not match:
            raise SystemExit("Could not parse version from blender_manifest.toml")
        return match.group(1)


def _included(path: Path) -> bool:
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return not any(part in EXCLUDE_NAMES for part in path.parts)


def build() -> Path:
    if not MANIFEST.exists():
        raise SystemExit(f"Manifest not found: {MANIFEST}")

    version = read_version()
    DIST_DIR.mkdir(exist_ok=True)
    out = DIST_DIR / f"magnets-{version}.zip"
    if out.exists():
        out.unlink()

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PKG_DIR.rglob("*")):
            if not path.is_file() or not _included(path):
                continue
            # Manifest at zip root -> arcname relative to PKG_DIR.
            zf.write(path, path.relative_to(PKG_DIR).as_posix())
            count += 1

        # GPL requires shipping the license text alongside the code. The
        # manifest only *declares* the SPDX id; the full text lives at the
        # zip root so every install carries it.
        if LICENSE_FILE.exists():
            zf.write(LICENSE_FILE, "LICENSE")
            count += 1
        else:
            raise SystemExit(f"LICENSE not found: {LICENSE_FILE}")

    print(f"Built {out.relative_to(REPO_ROOT)} ({count} files, v{version})")
    return out


if __name__ == "__main__":
    try:
        build()
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        raise
