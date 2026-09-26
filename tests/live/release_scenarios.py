"""Live release-path scenarios, run inside a *windowed* Blender.

The native-transform overlay only commits its snap when a real modal transform
ends, which needs an event loop, so ``--background`` cannot cover it. This
script drives Blender's own ``transform.*`` modals with simulated mouse events
(``--enable-event-simulate``) and checks where the selection lands.

Usage (see ``test_release_live.py``, which sets this up)::

    BLENDER_USER_RESOURCES=<tmp> blender --factory-startup --enable-event-simulate \
        --python tests/live/release_scenarios.py -- <magnets-zip> <scenario>

Prints ``LIVE_RESULT <scenario> PASS|FAIL <detail>`` and quits.
"""

import math
import sys

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

ZIP, SCENARIO = sys.argv[-2], sys.argv[-1]

_steps = []


def at(t):
    def deco(fn):
        _steps.append((t, fn))
        return fn

    return deco


def view3d():
    win = bpy.context.window_manager.windows[0]
    for area in win.screen.areas:
        if area.type == "VIEW_3D":
            reg = next(r for r in area.regions if r.type == "WINDOW")
            return win, area, reg, area.spaces.active.region_3d
    raise RuntimeError("no 3D viewport")


def win_xy(world):
    _win, _area, reg, rv3d = view3d()
    co = location_3d_to_region_2d(reg, rv3d, Vector(world))
    return int(reg.x + co.x), int(reg.y + co.y)


def mouse(xy):
    view3d()[0].event_simulate("MOUSEMOVE", "NOTHING", x=xy[0], y=xy[1])


def click(xy):
    win = view3d()[0]
    win.event_simulate("LEFTMOUSE", "PRESS", x=xy[0], y=xy[1])
    win.event_simulate("LEFTMOUSE", "RELEASE", x=xy[0], y=xy[1])


def result(ok, detail):
    print(f"LIVE_RESULT {SCENARIO} {'PASS' if ok else 'FAIL'} {detail}", flush=True)


def invoke(op, **props):
    win, area, reg, _rv3d = view3d()
    with bpy.context.temp_override(window=win, area=area, region=reg):
        op("INVOKE_DEFAULT", **props)


def cube():
    return bpy.data.objects["Cube"]


# ── Scenario definitions: (target location, target scale, native snap,
#    operator, operator props, mouse path builder, check) ───────────────────

def _line(a, b, n=10):
    a, b = win_xy(a), win_xy(b)
    return [(a[0] + (b[0] - a[0]) * i // n, a[1] + (b[1] - a[1]) * i // n)
            for i in range(n + 1)]


def _arc(center, radius, deg0, deg1, n=12):
    c = Vector(center)
    pts = []
    for i in range(n + 1):
        ang = math.radians(deg0 + (deg1 - deg0) * i / n)
        pts.append(win_xy(c + Vector((math.cos(ang), math.sin(ang), 0.0)) * radius))
    return pts


def _check_translate(loc):
    return abs(loc.y - 4.0) < 1e-6, f"y={loc.y:.4f} (want 4.0: snapped to Target)"


def _check_native(loc):
    # Blender's increment snap lands on whole units; Magnets must not move it.
    return abs(loc.y - round(loc.y)) < 1e-6, f"y={loc.y:.4f} (want a grid value)"


def _check_xlock(loc):
    return (abs(loc.y) < 1e-6 and abs(loc.x - 5.0) < 1e-6,
            f"loc=({loc.x:.4f}, {loc.y:.4f}) (want x=5 snapped, y=0 locked)")


def _check_rotate(_loc):
    z = math.degrees(cube().rotation_euler.z)
    return abs(z - 45.0) < 1e-3, f"rot_z={z:.3f} (want 45 exactly)"


def _check_scale(_loc):
    s = cube().scale.x
    return abs(s - 1.5) < 1e-5, f"scale={s:.5f} (want 1.5: Target's size)"


SCENARIOS = {
    # Drag toward Target's y: alignment snaps y to exactly 4.
    "translate": {"target": (5, 4, 0), "scale": 1.0, "native": False,
        "op": "translate", "props": {},
        "path": lambda: _line((0, 0, 0), (0.4, 3.93, 0)),
        "check": _check_translate},
    # Blender snapping on: Magnets stands aside.
    "yield": {"target": (5, 4, 0), "scale": 1.0, "native": True,
        "op": "translate", "props": {},
        "path": lambda: _line((0, 0, 0), (0.4, 3.93, 0)),
        "check": _check_native},
    # X lock: the Y alignment with Target (y=0.07) must not leak into the snap.
    # Midpoint/spacing are off so only the lock is under test: the resolver
    # currently stacks their X components onto the X alignment (known issue).
    "xlock": {"target": (5, 0.07, 0), "scale": 1.0, "native": False,
        "families_off": ("midpoint", "spacing"),
        "op": "translate", "props": {"constraint_axis": (True, False, False)},
        "path": lambda: _line((0, 0, 0), (4.93, 0.3, 0)),
        "check": _check_xlock},
    # Rotate to ~43 deg: snaps to the 15 deg increment (45).
    "rotate": {"target": (20, 20, 0), "scale": 1.0, "native": False,
        "op": "rotate", "props": {},
        "path": lambda: _arc((0, 0, 0), 3.0, 0.0, 43.0),
        "check": _check_rotate},
    # Scale to ~1.45: matches Target's size (scale 1.5).
    "scale": {"target": (8, 0, 0), "scale": 1.5, "native": False,
        "op": "resize", "props": {},
        "path": lambda: _line((3.0, 0, 0), (4.35, 0, 0)),
        "check": _check_scale},
}
spec = SCENARIOS[SCENARIO]
path = []


@at(0.5)
def install():
    bpy.ops.extensions.package_install_files(
        filepath=ZIP, repo="user_default", enable_on_install=True
    )
    import os

    if os.environ.get("MAGNETS_LIVE_DEBUG") == "1":
        bpy.context.preferences.addons["bl_ext.user_default.magnets"].preferences.debug = True


@at(1.0)
def setup():
    scene = bpy.context.scene
    scene.tool_settings.use_snap = spec["native"]
    for fid in spec.get("families_off", ()):
        setattr(scene.magnets, f"enable_{fid}", False)
    for obj in list(bpy.data.objects):
        if obj.name != "Cube":
            bpy.data.objects.remove(obj)
    c = cube()
    c.location = (0, 0, 0)
    c.rotation_euler = (0, 0, 0)
    c.scale = (1, 1, 1)
    bpy.ops.mesh.primitive_cube_add(location=spec["target"])
    target = bpy.context.active_object
    target.name = "Target"
    target.scale = (spec["scale"],) * 3
    bpy.ops.object.select_all(action="DESELECT")
    c.select_set(True)
    bpy.context.view_layer.objects.active = c
    _win, area, _reg, rv3d = view3d()
    rv3d.view_perspective = "ORTHO"
    rv3d.view_rotation = Quaternion((1, 0, 0, 0))  # top view
    rv3d.view_location = (2.5, 2.0, 0.0)
    rv3d.view_distance = 14.0
    area.tag_redraw()


@at(1.6)
def start():
    path.extend(spec["path"]())
    mouse(path[0])


@at(1.7)
def begin_transform():
    op = getattr(bpy.ops.transform, spec["op"])
    invoke(op, **spec["props"])


for _k in range(13):

    @at(1.9 + 0.08 * _k)
    def _move(k=_k):
        if k < len(path):
            mouse(path[k])


@at(3.2)
def release():
    click(path[-1])


@at(4.2)
def verify():
    ok, detail = spec["check"](cube().location)
    result(ok, detail)
    # Single undo step: one Ctrl+Z returns the whole move/rotate/scale.
    if ok and SCENARIO != "yield":
        win, area, reg, _rv3d = view3d()
        with bpy.context.temp_override(window=win, area=area, region=reg):
            bpy.ops.ed.undo()
        c = cube()
        back = (c.location.length < 1e-5 and abs(c.rotation_euler.z) < 1e-5
                and abs(c.scale.x - 1.0) < 1e-5)
        print(f"LIVE_RESULT {SCENARIO}-undo {'PASS' if back else 'FAIL'} "
              f"one undo -> loc={tuple(round(v, 4) for v in c.location)} "
              f"rot_z={c.rotation_euler.z:.4f} scale={c.scale.x:.4f}", flush=True)
    bpy.ops.wm.quit_blender()


@at(15.0)
def watchdog():
    result(False, "timed out")
    bpy.ops.wm.quit_blender()


for _t, _fn in _steps:
    bpy.app.timers.register(_fn, first_interval=_t)
