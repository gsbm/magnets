"""Headless coverage for the bpy-dependent runtime surface.

The fast unit suite only exercises the ``bpy``-free core. This module drives the
parts that *require* Blender - the crash-safe timer/draw wrappers, multi-window
viewport selection, the undo-collapse helpers, and object extraction - inside a
real ``blender --background`` process. Skipped when no Blender binary is found.

Point the runner at Blender via ``BLENDER_BIN`` or have ``blender`` on PATH.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Script executed *inside* Blender's Python.
INNER = rf"""
import sys
sys.path.insert(0, r"{REPO_ROOT!s}")

import bpy
import magnets
magnets.register()

from magnets import transform_overlay as ov
from magnets.draw import handler as draw
from magnets.adapters.extract import object_feature_pool


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ── Crash safety: a raising timer tick must never escape ─────────────────────
calls = {{"n": 0}}


def _boom():
    calls["n"] += 1
    raise RuntimeError("synthetic tick failure")


ov._timer_callback_inner = _boom
ov._consec_failures = 0
ov._errors_logged = 0

for _ in range(ov._MAX_CONSEC_FAILURES + 2):
    interval = ov._timer_callback()  # must not raise
    check(isinstance(interval, float), "timer wrapper must return a float delay")

check(calls["n"] >= ov._MAX_CONSEC_FAILURES, "inner tick should have been called")
check(
    ov._timer_callback() == ov._FAILURE_COOLDOWN,
    "wrapper should back off to the cooldown heartbeat after repeated failures",
)

# Pure helper contract
check(ov._failure_interval(0) == 0.1, "single failure keeps a fast retry")
check(
    ov._failure_interval(ov._MAX_CONSEC_FAILURES) == ov._FAILURE_COOLDOWN,
    "hitting the failure ceiling returns the cooldown",
)

# A clean tick self-heals the breaker.
ov._timer_callback_inner = lambda: 0.5
ov._consec_failures = 99
check(ov._timer_callback() == 0.5, "clean tick returns inner interval")
check(ov._consec_failures == 0, "clean tick resets the failure counter")


# ── Crash safety: a raising draw handler must never escape ───────────────────
_orig_draw_view = draw._draw_view


def _draw_boom():
    raise RuntimeError("synthetic draw failure")


draw._draw_view = _draw_boom
draw._safe_draw_view()  # must not raise
draw._draw_view = _orig_draw_view


# ── Multi-window viewport selection is safe and self-consistent ──────────────
result = ov._view3d_context(bpy.context)
check(isinstance(result, tuple) and len(result) == 3, "viewport scan returns a 3-tuple")
area, region, rv3d = result
viewports = list(ov._iter_view3d(bpy.context))
if area is None:
    check(viewports == [], "no chosen viewport implies none were found")
else:
    check(region is not None and rv3d is not None, "chosen viewport is complete")
    check(len(viewports) >= 1, "iter must see the chosen viewport")
    largest = max(r.width * r.height for _, r, _ in viewports)
    check(region.width * region.height == largest, "chosen viewport is the largest")


# ── Object extraction produces features ──────────────────────────────────────
bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
cube = bpy.context.active_object
pool = object_feature_pool(cube)
check(len(pool.points) > 0, "cube extraction should yield point features")
check(any(p.co is not None for p in pool.points), "extracted points carry coords")


# ── Undo-collapse helpers operate on live objects ────────────────────────────
import math

from mathutils import Matrix, Vector

start_matrices = {{cube.name: cube.matrix_world.copy()}}
check(ov._returned_to_start(start_matrices) is True, "unmoved object reads as at-start")
cube.location = Vector((5.0, 0.0, 0.0))
bpy.context.view_layer.update()
check(ov._returned_to_start(start_matrices) is False, "moved object is not at start")

target = {{cube.name: Matrix.Translation((2.0, 3.0, 4.0))}}
ov._apply_final_poses(target)
bpy.context.view_layer.update()
check(
    (cube.matrix_world.translation - Vector((2.0, 3.0, 4.0))).length < 1e-5,
    "final-pose application moves the object to the requested world position",
)

# Rotate commit math: a full final pose carries orientation, not just position.
rot_pose = ov.rotated_matrix(
    Matrix.Identity(4), Vector((0.0, 0.0, 1.0)), math.radians(90), Vector((0, 0, 0))
)
ov._apply_final_poses({{cube.name: rot_pose}})
bpy.context.view_layer.update()
check(
    abs(cube.rotation_euler.z - math.radians(90)) < 1e-4,
    "rotate pose application orients the object",
)

# Scale commit math: a uniform scale pose feeds through to the object's scale.
cube.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()
scale_pose = ov.scaled_matrix(cube.matrix_world, 2.0, Vector((0.0, 0.0, 0.0)))
ov._apply_final_poses({{cube.name: scale_pose}})
bpy.context.view_layer.update()
check(
    abs(max(cube.scale) - 2.0) < 1e-4,
    "scale pose application resizes the object",
)

# Nearby-size gather sees a second object and excludes the moving one.
bpy.ops.mesh.primitive_cube_add(location=(10.0, 0.0, 0.0))
neighbour = bpy.context.active_object
neighbour.scale = (3.0, 3.0, 3.0)
bpy.context.view_layer.update()
dims = ov._nearby_dimensions(bpy.context, Vector((0.0, 0.0, 0.0)), frozenset({{cube.name}}))
check(len(dims) >= 1, "nearby-size gather finds the neighbour")
check(any(abs(d - 6.0) < 1e-3 for d in dims), "neighbour size (3x 2m cube = 6m) is gathered")

magnets.unregister()
print("MAGNETS_RUNTIME_OK")
"""


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.mark.integration
def test_runtime_headless(tmp_path):
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
    assert "MAGNETS_RUNTIME_OK" in proc.stdout, "runtime headless checks failed"
