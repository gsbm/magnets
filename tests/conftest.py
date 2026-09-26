"""Pytest setup for the bpy-free unit suite.

Adds ``magnets/`` to ``sys.path`` so the inference core imports as a
top-level ``core`` package, without the add-on entry point (which needs
``bpy``).
"""

import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent.parent / "magnets"

if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))
