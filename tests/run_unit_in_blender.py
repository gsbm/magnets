"""Minimal test runner for Blender's embedded Python (no pytest required)."""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "magnets"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))


def _load_tests():
    unit = REPO / "tests" / "unit"
    modules = sorted(unit.glob("test_*.py"))
    for path in modules:
        name = f"tests.unit.{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        yield mod


def main() -> int:
    passed = 0
    failed = 0
    for mod in _load_tests():
        for attr in dir(mod):
            if not attr.startswith("test_"):
                continue
            fn = getattr(mod, attr)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
                print(f"PASS {mod.__name__}.{attr}")
            except Exception:
                failed += 1
                print(f"FAIL {mod.__name__}.{attr}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
