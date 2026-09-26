"""Enforce that the inference core never imports bpy.

This keeps ``magnets/core/`` unit-testable without Blender.
"""

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[2] / "magnets" / "core"


def _core_py_files():
    return sorted(CORE_DIR.rglob("*.py"))


def test_core_directory_exists():
    assert CORE_DIR.is_dir()
    assert _core_py_files(), "expected at least one module under magnets/core"


def test_core_imports_without_bpy():
    # Importable as a top-level package thanks to conftest's sys.path entry.
    import core  # noqa: F401
    from core import families

    assert families.FAMILY_IDS


def test_no_module_under_core_imports_bpy():
    offenders = []
    for path in _core_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [n.name for n in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(n == "bpy" or n.startswith("bpy.") for n in names):
                offenders.append(path.name)
    assert not offenders, f"bpy imported under core/: {offenders}"
