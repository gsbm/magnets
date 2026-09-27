"""Headless coverage for scene adapters and preference toggles.

Covers non-mesh feature extraction (armature, curves, text, light, camera,
empty, lattice, other types), every alignment frame, scene-unit labels,
the Precision Mode / debug preference callbacks, and the Precision Mode
operators' poll gating and header helpers. Skipped when no Blender
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
import math
import sys
from types import SimpleNamespace

sys.path.insert(0, r"{REPO_ROOT!s}")

import addon_utils
import bpy
from mathutils import Euler, Matrix, Vector

addon_utils.enable("magnets", default_set=True)

from magnets import keymaps, log
from magnets.adapters import entities
from magnets.adapters.extract import candidate_feature_pool
from magnets.adapters.frames import frame_axes
from magnets.adapters.units import length_formatter, scene_unit_info
from magnets.core.features import PointKind
from magnets.core.frames import Frame
from magnets.preferences import get_prefs
from magnets.properties import custom_frame_object


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def close(a, b, eps=1e-5):
    return (Vector(a) - Vector(b)).length < eps


scene = bpy.context.scene
coll = scene.collection
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)


def link(obj, location=(0.0, 0.0, 0.0)):
    obj.location = location
    coll.objects.link(obj)
    bpy.context.view_layer.update()
    return obj


# ── Entities: armature ───────────────────────────────────────────────────────
arm_data = bpy.data.armatures.new("ArmData")
arm = link(bpy.data.objects.new("Arm", arm_data), (1.0, 0.0, 0.0))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for i, name in enumerate(("Root", "Tip")):
    eb = arm_data.edit_bones.new(name)
    eb.head = (0.0, 0.0, float(i))
    eb.tail = (0.0, 0.0, float(i) + 1.0)
# Bones that do not inherit scale are still snappable.
arm_data.edit_bones["Tip"].inherit_scale = "NONE"
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

pool = entities.entity_feature_pool(arm)
heads = sorted(tuple(round(c, 5) for c in p.co) for p in pool.points)
check(heads == [(1.0, 0.0, 0.0), (1.0, 0.0, 1.0)], f"bone heads: {{heads}}")
check(all(p.kind == PointKind.BONE for p in pool.points), "bone point kind")
check(len(pool.lines) == 2, f"one line per bone, got {{len(pool.lines)}}")
check(all(close(l.direction, (0, 0, 1)) for l in pool.lines), "bone directions")

empty_arm = link(bpy.data.objects.new("ArmEmpty", bpy.data.armatures.new("E")), (0, 5, 0))
pool = entities.entity_feature_pool(empty_arm)
check(len(pool.points) == 1 and pool.points[0].kind == PointKind.ORIGIN,
      "armature without bones falls back to its origin")
check(close(pool.points[0].co, (0, 5, 0)), "fallback origin location")
check(not entities.armature_feature_pool(link(bpy.data.objects.new("NotArm", None))).points,
      "armature extractor ignores other types")

# ── Entities: curves (bezier is 3D, poly/NURBS points are 4D) ────────────────
bez = bpy.data.curves.new("Bez", "CURVE")
spline = bez.splines.new("BEZIER")
spline.bezier_points.add(1)
spline.bezier_points[0].co = (0.0, 0.0, 0.0)
spline.bezier_points[1].co = (2.0, 0.0, 0.0)
bez_obj = link(bpy.data.objects.new("BezObj", bez), (0.0, 1.0, 0.0))
pool = entities.entity_feature_pool(bez_obj)
cos = sorted(tuple(round(c, 5) for c in p.co) for p in pool.points)
check(cos == [(0.0, 1.0, 0.0), (2.0, 1.0, 0.0)], f"bezier points: {{cos}}")
check(all(p.kind == PointKind.CURVE for p in pool.points), "curve point kind")

nurbs = bpy.data.curves.new("Nurbs", "CURVE")
spline = nurbs.splines.new("NURBS")
spline.points.add(1)
spline.points[0].co = (1.0, 2.0, 3.0, 1.0)
spline.points[1].co = (4.0, 5.0, 6.0, 0.5)
nurbs_obj = link(bpy.data.objects.new("NurbsObj", nurbs), (10.0, 0.0, 0.0))
pool = entities.entity_feature_pool(nurbs_obj)
check(all(len(p.co) == 3 for p in pool.points), "NURBS features must be 3D points")
cos = sorted(tuple(round(c, 5) for c in p.co) for p in pool.points)
check(cos == [(11.0, 2.0, 3.0), (14.0, 5.0, 6.0)], f"NURBS points: {{cos}}")

text = link(bpy.data.objects.new("Text", bpy.data.curves.new("T", "FONT")), (0, 0, 7))
pool = entities.entity_feature_pool(text)
check([p.kind for p in pool.points] == [PointKind.ORIGIN], "text falls back to origin")
check(not entities.curve_feature_pool(arm).points, "curve extractor ignores armatures")

# ── Entities: light / camera / empty / lattice / other ───────────────────────
light = link(bpy.data.objects.new("Lamp", bpy.data.lights.new("L", "SUN")), (0, 0, 3))
light.rotation_euler = Euler((math.pi / 2, 0.0, 0.0))
bpy.context.view_layer.update()
pool = entities.entity_feature_pool(light)
check([p.kind for p in pool.points] == [PointKind.ORIGIN], "light origin")
check(len(pool.directions) == 1 and pool.directions[0].kind == "light_axis", "light axis")
# -Z rotated +90° about X points along +Y.
check(close(pool.directions[0].direction, (0, 1, 0)), "light axis follows rotation")

cam = link(bpy.data.objects.new("Cam", bpy.data.cameras.new("C")), (0, -4, 0))
pool = entities.entity_feature_pool(cam)
check(len(pool.directions) == 1 and pool.directions[0].kind == "camera_axis", "camera axis")
check(close(pool.directions[0].direction, (0, 0, -1)), "camera looks down -Z")

for name, data in (
    ("Empty", None),
    ("Lattice", bpy.data.lattices.new("Lat")),
    ("Speaker", bpy.data.speakers.new("Spk")),
):
    obj = link(bpy.data.objects.new(name, data), (3, 3, 3))
    pool = entities.entity_feature_pool(obj)
    check([p.kind for p in pool.points] == [PointKind.ORIGIN], f"{{name}} origin")
    check(close(pool.points[0].co, (3, 3, 3)), f"{{name}} origin location")
    check(not pool.directions, f"{{name}} has no direction")

# A scene mixing every type still builds one candidate pool (one raising
# extractor used to abort the whole snapshot).
pool = candidate_feature_pool(bpy.context, exclude=[])
names = {{p.entity for p in pool.points}}
for expected in ("Arm", "BezObj", "NurbsObj", "Text", "Lamp", "Cam", "Empty", "Speaker"):
    check(expected in names, f"{{expected}} missing from candidate pool: {{sorted(names)}}")


# ── Frames ───────────────────────────────────────────────────────────────────
def axes_close(axes, x, y, z):
    return close(axes["X"], x) and close(axes["Y"], y) and close(axes["Z"], z)


WORLD = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
ROT_Z90 = ((0, 1, 0), (-1, 0, 0), (0, 0, 1))
ROT_X90 = ((1, 0, 0), (0, 0, 1), (0, -1, 0))

parent = link(bpy.data.objects.new("Parent", None))
parent.rotation_euler = Euler((0.0, 0.0, math.pi / 2))
child = link(bpy.data.objects.new("Child", None), (1, 0, 0))
child.parent = parent
child.rotation_euler = Euler((math.pi / 2, 0.0, 0.0))
bpy.context.view_layer.update()
ctx = bpy.context

check(axes_close(frame_axes(ctx, child, Frame.WORLD), *WORLD), "world frame")
# Child world rotation = Rz(90) @ Rx(90).
local = frame_axes(ctx, child, Frame.LOCAL)
check(axes_close(local, (0, 1, 0), (0, 0, 1), (1, 0, 0)), f"local frame: {{local}}")
check(axes_close(frame_axes(ctx, child, Frame.PARENT), *ROT_Z90), "parent frame")
check(axes_close(frame_axes(ctx, parent, Frame.PARENT), *ROT_Z90),
      "parent frame without a parent uses the object's own axes")

check(axes_close(frame_axes(SimpleNamespace(region_data=None), child, Frame.VIEW), *WORLD),
      "view frame without a viewport falls back to world")
view = Matrix.Rotation(-math.pi / 2, 4, "Z")  # view matrix = inverse of camera rotation
fake = SimpleNamespace(region_data=SimpleNamespace(view_matrix=view))
check(axes_close(frame_axes(fake, child, Frame.VIEW), *ROT_Z90), "view frame")

check(axes_close(frame_axes(ctx, child, Frame.COLLECTION), *WORLD),
      "collection frame without an instancer is world")
inst_coll = bpy.data.collections.new("Kit")
scene.collection.children.link(inst_coll)
member = bpy.data.objects.new("Member", None)
inst_coll.objects.link(member)
instancer = link(bpy.data.objects.new("Instancer", None), (5, 0, 0))
instancer.instance_type = "COLLECTION"
instancer.instance_collection = inst_coll
instancer.rotation_euler = Euler((math.pi / 2, 0.0, 0.0))
bpy.context.view_layer.update()
check(axes_close(frame_axes(ctx, member, Frame.COLLECTION), *ROT_X90), "collection frame")

check(axes_close(frame_axes(ctx, child, Frame.CUSTOM), *WORLD), "custom frame fallback")
check(axes_close(frame_axes(ctx, child, Frame.CUSTOM, custom_object=parent), *ROT_Z90),
      "custom frame from object")
check(axes_close(frame_axes(ctx, child, Frame.CUSTOM,
                            custom_matrix=Matrix.Rotation(math.pi / 2, 4, "X")), *ROT_X90),
      "custom frame from matrix")

opts = scene.magnets
opts.custom_frame_object = parent
check(custom_frame_object(ctx, opts) == parent, "custom frame object in view layer")
orphan = bpy.data.objects.new("Orphan", None)  # not linked to any scene
opts.custom_frame_object = orphan
check(custom_frame_object(ctx, opts) is None, "unlinked custom frame object is ignored")
opts.custom_frame_object = None
check(custom_frame_object(ctx, opts) is None, "no custom frame object")


# ── Units ────────────────────────────────────────────────────────────────────
us = scene.unit_settings
us.system, us.scale_length = "METRIC", 1.0
check(scene_unit_info(ctx) == (1.0, "m"), "metric unit info")
metric = length_formatter(ctx)(1.5)
check("m" in metric and "1.5" in metric, f"metric label: {{metric!r}}")
us.scale_length = 0.001
scale, suffix = scene_unit_info(ctx)
check(suffix == "m" and abs(scale - 0.001) < 1e-9, "scaled metric unit info")
check("mm" in length_formatter(ctx)(1.5), "unit scale changes the label")

us.system, us.scale_length = "IMPERIAL", 1.0
scale, suffix = scene_unit_info(ctx)
check(suffix == "ft" and abs(scale - 3.28084) < 1e-6, "imperial unit info")
imperial = length_formatter(ctx)(1.0)
check(imperial != metric and ("'" in imperial or '"' in imperial or "ft" in imperial),
      f"imperial label: {{imperial!r}}")

us.system = "NONE"
check(scene_unit_info(ctx) == (1.0, "bu"), "unitless info")
plain = length_formatter(ctx)(2.0)
check(plain.startswith("2") and "m" not in plain, f"unitless label: {{plain!r}}")
us.system = "METRIC"


# ── Precision Mode and debug preferences ─────────────────────────────────────
prefs = get_prefs(ctx)
bound = {{kmi.idname: kmi for _km, kmi in keymaps._addon_keymaps}}
check(set(bound) == {{"magnets.translate", "magnets.rotate", "magnets.scale"}},
      f"precision keymap items: {{sorted(bound)}}")
check(len(keymaps._toggle_keymaps) == 1, "on/off toggle shortcut registered")
toggle = keymaps._toggle_keymaps[0][1]
check(toggle.idname == keymaps.TOGGLE_IDNAME and toggle.active, "toggle is always active")

check(not prefs.precision_mode, "Precision Mode is off by default")
check(not any(k.active for k in bound.values()), "G/R/S stay native by default")
prefs.precision_mode = True
check(all(k.active for k in bound.values()), "Precision Mode binds G/R/S")
check(toggle.active, "toggle unaffected by Precision Mode")
prefs.precision_mode = False
check(not any(k.active for k in bound.values()), "turning it off restores native G/R/S")

prefs.debug = True
check(log.debug_enabled(), "debug preference enables debug logging")
prefs.debug = False
check(not log.debug_enabled(), "debug preference off disables debug logging")

# The toggle operator flips the scene switch.
enabled = opts.enabled
bpy.ops.magnets.toggle()
check(opts.enabled != enabled, "toggle operator flips Magnets on/off")
bpy.ops.magnets.toggle()
check(opts.enabled == enabled, "toggle operator flips back")

# ── Precision Mode operators: poll gating and header helpers ─────────────────
from magnets.ops import modal_common
from magnets.ops.modal_mesh_ops import MAGNETS_OT_extrude
from magnets.ops.modal_rotate import MAGNETS_OT_rotate
from magnets.ops.modal_scale import MAGNETS_OT_scale
from magnets.ops.modal_translate import MAGNETS_OT_translate

mesh_obj = link(bpy.data.objects.new("MeshObj", bpy.data.meshes.new("M")))
VIEW3D = SimpleNamespace(type="VIEW_3D")


def fake_ctx(mode="OBJECT", obj=mesh_obj, space=VIEW3D):
    return SimpleNamespace(mode=mode, active_object=obj, space_data=space, scene=scene)


opts.enabled = True
for op in (MAGNETS_OT_translate, MAGNETS_OT_rotate, MAGNETS_OT_scale):
    name = op.__name__
    check(op.poll(fake_ctx()), f"{{name}} runs in object mode")
    check(not op.poll(fake_ctx(obj=None)), f"{{name}} needs an active object")
    check(not op.poll(fake_ctx(space=SimpleNamespace(type="IMAGE_EDITOR"))),
          f"{{name}} is 3D View only")
    check(not op.poll(fake_ctx(mode="POSE")), f"{{name}} falls back to native in pose mode")
check(MAGNETS_OT_translate.poll(fake_ctx(mode="EDIT_MESH")), "translate runs in mesh edit")
check(not MAGNETS_OT_translate.poll(fake_ctx(mode="EDIT_MESH", obj=cam)),
      "edit-mode translate needs a mesh")
for op in (MAGNETS_OT_rotate, MAGNETS_OT_scale):
    check(not op.poll(fake_ctx(mode="EDIT_MESH")), f"{{op.__name__}} is native in edit mode")
check(not MAGNETS_OT_translate.poll(fake_ctx(space=None)), "translate without a space")

opts.enabled = False
for op in (MAGNETS_OT_translate, MAGNETS_OT_rotate, MAGNETS_OT_scale):
    check(not op.poll(fake_ctx()), f"{{op.__name__}} defers to native when Magnets is off")
opts.enabled = True

check(MAGNETS_OT_extrude.poll(fake_ctx(mode="EDIT_MESH")), "extrude runs in mesh edit")
check(not MAGNETS_OT_extrude.poll(fake_ctx()), "extrude needs edit mode")

text = modal_common.header_text("Magnets Move", "X", "Dx 1.000", True)
check(text.startswith("Magnets Move [X]: Dx 1.000") and "X/Y/Z" in text and "Snapped" in text,
      f"header text: {{text!r}}")
text = modal_common.header_text("Magnets Move", "", "Dx 1.000", False)
check("[" not in text and "Snapped" not in text, f"plain header text: {{text!r}}")

calls = []
area = SimpleNamespace(header_text_set=calls.append)
modal_common.set_header(SimpleNamespace(area=area), "hello")
modal_common.clear_header(SimpleNamespace(area=area))
check(calls == ["hello", None], f"header set/clear: {{calls}}")
modal_common.set_header(SimpleNamespace(area=None), "ignored")  # must not raise
modal_common.clear_header(SimpleNamespace())

addon_utils.disable("magnets", default_set=True)
check(not keymaps._addon_keymaps and not keymaps._toggle_keymaps,
      "keymap items removed on unregister")
print("MAGNETS_ADAPTERS_OK")
"""


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.mark.integration
def test_scene_adapters_headless(tmp_path):
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
    assert "MAGNETS_ADAPTERS_OK" in proc.stdout, "scene adapter checks failed"
