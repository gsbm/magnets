"""Pytest setup for the bpy-free unit suite.

Adds the ``magnets/`` package directory to ``sys.path`` so the inference core
imports as a top-level ``core`` package without pulling in the add-on entry
point (which requires ``bpy``). This mirrors decision 1.2 in PLAN.md: the core
runs and is tested without Blender.
"""

import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent.parent / "magnets"

if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))
