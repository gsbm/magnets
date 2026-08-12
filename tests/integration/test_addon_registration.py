"""Headless registration smoke test.

Runs the add-on inside a real Blender in background mode: register, invoke the
placeholder operator, unregister. Skipped automatically when no Blender binary
is available (so the fast unit suite stays dependency-free).

Point the runner at Blender via the ``BLENDER_BIN`` env var, or have ``blender``
on PATH.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Script executed *inside* Blender's Python.
INNER = f"""
import sys
sys.path.insert(0, r"{REPO_ROOT!s}")
import magnets
magnets.register()
import bpy
assert hasattr(bpy.ops.magnets, "translate"), "translate op missing"
assert hasattr(bpy.ops.magnets, "rotate"), "rotate op missing"
assert hasattr(bpy.ops.magnets, "scale"), "scale op missing"
assert hasattr(bpy.ops.magnets, "extrude"), "extrude op missing"
assert hasattr(bpy.ops.magnets, "options_preset"), "preset op missing"
assert hasattr(bpy.ops.magnets, "options_reset"), "reset op missing"
res = bpy.ops.magnets.noop()
assert res == {{'FINISHED'}}, res

# Presets and reset drive the scene options.
opts = bpy.context.scene.magnets
opts.snap_tolerance_px = 99
bpy.ops.magnets.options_preset(preset='PRECISE')
assert opts.snap_tolerance_px == 8, opts.snap_tolerance_px
bpy.ops.magnets.options_reset()
assert opts.snap_tolerance_px == 16, opts.snap_tolerance_px

magnets.unregister()
print("MAGNETS_SMOKE_OK")
"""


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.mark.integration
def test_register_invoke_unregister(tmp_path):
    blender = _blender_bin()
    if not blender:
        pytest.skip("no Blender binary (set BLENDER_BIN or add blender to PATH)")

    script = tmp_path / "inner.py"
    script.write_text(INNER, encoding="utf-8")

    proc = subprocess.run(
        [blender, "--background", "--factory-startup", "--python", str(script)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    assert "MAGNETS_SMOKE_OK" in proc.stdout, "registration smoke test failed"
