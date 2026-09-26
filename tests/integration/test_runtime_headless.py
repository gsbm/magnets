"""Headless coverage for the bpy-dependent runtime.

Runs the crash-safe timer/draw wrappers, viewport selection, undo-collapse
helpers and extraction in ``blender --background``. Skipped when no Blender
binary is found (``BLENDER_BIN`` or ``blender`` on PATH).
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
dims = ov._nearby_dimensions(bpy.context, frozenset({{cube.name}}))
check(len(dims) >= 1, "nearby-size gather finds the neighbour")
check(cube.name not in {{n for n, _ in dims}}, "moving object is excluded")
check(
    any(n == neighbour.name and abs(d - 6.0) < 1e-3 for n, d in dims),
    "neighbour size (3x 2m cube = 6m) is gathered with its name",
)

# Landing-preview outline: 12 bbox edges per object, placed at the final pose.
edges = ov._pose_edges({{cube.name: Matrix.Translation((100.0, 0.0, 0.0))}})
check(len(edges) == 12, "a box outline has 12 edges")
check(all(a.x > 90.0 and b.x > 90.0 for a, b in edges), "outline sits at the final pose")
check(
    all(sum(1 for i in range(3) if abs(a[i] - b[i]) > 1e-6) == 1 for a, b in edges),
    "outline edges are box edges, not face diagonals",
)

# Extraction: a cube's bbox face centers include its top and bottom faces.
from magnets.core.features import PointKind

cube.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()
faces = [p.co for p in object_feature_pool(cube).points if p.kind == PointKind.BBOX_FACE_CENTER]
check(
    any(abs(c.z - 1.0) < 1e-4 and abs(c.x) < 1e-4 and abs(c.y) < 1e-4 for c in faces),
    "top face center (0, 0, 1) is extracted",
)

# ── Native operator property reads (C ops expose them on .properties) ─────────
class _Props:
    snap = True
    constraint_axis = (True, False, False)
    orient_type = "GLOBAL"


class _COp:
    bl_idname = "TRANSFORM_OT_translate"
    properties = _Props()


class _PyOp:
    bl_idname = "TRANSFORM_OT_translate"
    snap = False


check(ov._op_prop(_COp(), "snap") is True, "C-op props are read from .properties")
check(ov._op_prop(_PyOp(), "snap") is False, "Python-op props are read directly")
check(ov._op_prop(_PyOp(), "missing") is None, "unknown props read as None")


# ── Yield to Blender snapping ─────────────────────────────────────────────────
from magnets.properties import get_options

opts = get_options(bpy.context)
ts = bpy.context.scene.tool_settings
ts.use_snap = True
check(ov._yield_to_native_snap(bpy.context, opts, finished=False), "yields when snapping on")
opts.defer_to_native_snap = False
check(not ov._yield_to_native_snap(bpy.context, opts, finished=False), "opt-out respected")
opts.defer_to_native_snap = True
ts.use_snap = False
check(not ov._yield_to_native_snap(bpy.context, opts, finished=True), "no yield when off")


# ── Presets: Balanced is the defaults, and the active one is detected ────────
from magnets.ops.presets import matching_preset

bpy.ops.magnets.options_reset()
check(matching_preset(opts) == "BALANCED", "defaults must equal the Balanced preset")
bpy.ops.magnets.options_preset(preset="LOOSE")
check(matching_preset(opts) == "LOOSE", "applied preset is detected as active")
opts.snap_tolerance_px = 17
check(matching_preset(opts) is None, "customised values match no preset")
bpy.ops.magnets.options_reset()


# ── Custom alignment frame is an object pointer ──────────────────────────────
from magnets.properties import custom_frame_object

check(custom_frame_object(bpy.context, opts) is None, "no custom frame by default")
opts.custom_frame_object = neighbour
check(custom_frame_object(bpy.context, opts) == neighbour, "custom frame resolves")
opts.custom_frame_object = None


# ── Labels use scene units; UI scale falls back to 1 headless ────────────────
from magnets.adapters.units import length_formatter
from magnets.adapters.view import pixel_size, ui_scale

units = bpy.context.scene.unit_settings
units.system = "METRIC"
units.scale_length = 1.0
fmt = length_formatter(bpy.context)
check(fmt(0.123) == "12.3 cm", f"metric label, got {{fmt(0.123)!r}}")
units.system = "NONE"
check(length_formatter(bpy.context)(0.5) == "0.5", "unitless label is a plain number")
units.system = "METRIC"
check(ui_scale(bpy.context) > 0 and pixel_size(bpy.context) > 0, "positive UI scale")

# ── Panels draw without error (recording layout; no UI headless) ─────────────
from magnets.ui import panel as ui_panel

_icons = set(bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items.keys())
_drawn = []


class _Layout:
    use_property_split = False
    use_property_decorate = False
    active = True

    def _child(self, *args, **kwargs):
        return _Layout()

    row = column = grid_flow = _child

    def prop(self, data, name, **kwargs):
        check(hasattr(data, name), f"panel draws unknown property {{name!r}}")
        _drawn.append(name)

    def label(self, text="", icon="NONE", **kwargs):
        check(icon in _icons, f"unknown icon {{icon!r}}")
        _drawn.append(text)

    def operator(self, idname, text="", icon="NONE", **kwargs):
        check(icon in _icons, f"unknown icon {{icon!r}}")
        return type("OpProps", (), {{}})()

    def separator(self, **kwargs):
        pass

    def popover(self, panel, **kwargs):
        check(hasattr(bpy.types, panel), f"popover of unknown panel {{panel!r}}")


class _Self:
    layout = _Layout()


# Registered as a plain module here (not an enabled add-on), so there are no
# AddonPreferences; stand in the fields the panels read.
import types

ui_panel.get_prefs = lambda _ctx: types.SimpleNamespace(
    precision_mode=False, guide_fade_passive=True, show_header_toggle=True
)
ts.use_snap = True
for cls in ui_panel._CLASSES:
    cls.draw(_Self(), bpy.context)
ts.use_snap = False
check("defer_to_native_snap" in _drawn, "snapping panel offers the yield toggle")
ui_panel.draw_view3d_header(_Self(), bpy.context)  # header button + popover

# ── On/off toggle operator ───────────────────────────────────────────────────
was = opts.enabled
bpy.ops.magnets.toggle()
check(opts.enabled is (not was), "toggle flips Magnets on/off")
bpy.ops.magnets.toggle()
check(opts.enabled is was, "toggle flips back")
check(
    "Blender snapping takes over" in _drawn,
    "panel explains when Blender snapping takes over",
)

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
        check=False,
        timeout=300,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    assert "MAGNETS_RUNTIME_OK" in proc.stdout, "runtime headless checks failed"
