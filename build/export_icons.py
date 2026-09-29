#!/usr/bin/env python3
"""Write ``landing/icons.svg`` from the guide icons in ``magnets/core/icons.py``.

The viewport draws the same definitions, so the site and the add-on always
match. ``--check`` exits non-zero when the committed sprite is out of date.

Usage: ``python build/export_icons.py [--check]``
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPRITE = REPO_ROOT / "landing" / "icons.svg"


def load_icons():
    # Load the module by path: it is bpy-free, but importing the ``magnets``
    # package would pull in bpy.
    path = REPO_ROOT / "magnets" / "core" / "icons.py"
    spec = importlib.util.spec_from_file_location("magnets_core_icons", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look the module up by name
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    text = load_icons().sprite()
    if "--check" in argv:
        current = SPRITE.read_text(encoding="utf-8") if SPRITE.exists() else ""
        if current != text:
            print(f"{SPRITE.relative_to(REPO_ROOT)} is out of date: run python build/export_icons.py")
            return 1
        print(f"{SPRITE.relative_to(REPO_ROOT)} is up to date")
        return 0
    SPRITE.write_text(text, encoding="utf-8")
    print(f"Wrote {SPRITE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
