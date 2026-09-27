"""Blender-side script for ``test_release_commit_headless.py``.

Drives the snap-on-release path (session start, drag ticks, release commit and
the timer state machine) in ``blender --background``. There is no window, so a
synthetic region/view is passed in. Each simulated native transform pushes an
undo step like Blender does, so the one-step undo collapse runs for real.

Usage: blender --background --factory-startup --python <this> -- <repo root>
"""

import math
import sys
from pathlib import Path

REPO_ROOT = sys.argv[sys.argv.index("--") + 1]
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import addon_utils
import bmesh
import bpy
from mathutils import Vector

addon_utils.enable("magnets", default_set=True)

from fake_view import FRONT, PERSP, TOP

from magnets import transform_overlay as ov
from magnets.draw import handler as draw
from magnets.properties import get_options

failures: list[str] = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"CHECK FAILED: {msg}", flush=True)


def close(a, b, eps=1e-4):
    return (Vector(a) - Vector(b)).length < eps


# ── Scene ────────────────────────────────────────────────────────────────────
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)


def add_cube(name, location):
    bpy.ops.mesh.primitive_cube_add(location=location)  # 2 m cube
    bpy.context.active_object.name = name


add_cube("Target", (0.0, 5.0, 0.0))  # the snap reference
add_cube("Mover", (4.0, 0.0, 0.0))
add_cube("Mover2", (4.0, -3.0, 0.0))
add_cube("Big", (-6.0, -6.0, 0.0))
bpy.data.objects["Big"].scale = (3.0, 3.0, 3.0)  # 6 m: the scale-match reference
bpy.context.view_layer.update()
START = {o.name: o.matrix_world.copy() for o in bpy.data.objects}


# Undo reloads scene data and invalidates Python references to it, so every
# data-block is looked up fresh.
def ob(name):
    return bpy.data.objects[name]


def opts():
    return get_options(bpy.context)


def ts():
    return bpy.context.scene.tool_settings


def push(label):
    """Record an undo step, as Blender does after every finished operator."""
    bpy.ops.ed.undo_push(message=label)


def reset(selected=("Mover",), active=None):
    ov._end_session()
    draw.clear_state()
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.view_layer.objects:
        if o.name in START:
            o.matrix_world = START[o.name].copy()
        o.select_set(o.name in selected)
    bpy.context.view_layer.objects.active = ob(active or selected[0])
    opts().enabled = True
    opts().soft_snap = True
    ts().use_snap = False
    bpy.context.view_layer.update()
    push("reset")


def move(*objs, by, record=True):
    """Move like a finished native transform, which pushes its own undo step."""
    for o in objs:
        o.location = o.location + Vector(by)
    bpy.context.view_layer.update()
    if record:
        push("native move")


def begin(op="TRANSFORM_OT_translate", view=TOP):
    ov._begin_session(bpy.context, op, view=view)
    check(ov._session is not None, f"{op}: session starts")


def release(view=TOP):
    ov._commit_release(bpy.context, view=view)
    bpy.context.view_layer.update()


def loc(ob):
    return ob.matrix_world.translation.copy()


# ── Translate: snap on release ───────────────────────────────────────────────
# Mover lands 0.15 m (7.5 px) off Target's X column: X snaps, Y/Z stay.
reset()
begin()
check(ov._session.start_anchor is not None and close(ov._session.start_anchor, (4, 0, 0)),
      "session records the start anchor")
check(ov._session.world_tol and ov._session.world_tol > 0, "session freezes a world tolerance")
check(set(ov._session.start_matrices) == {"Mover"}, "start pose captured for the mover")
check("Mover" not in {p.entity for p in ov._session.snapshot.pool.points},
      "moving object is excluded from the candidates")
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
release()
check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)), f"translate snaps X onto Target: {tuple(loc(ob('Mover')))}")
check(ov._session.committed, "session marked committed")
check(close(loc(ob("Target")), (0, 5, 0)), "the snap reference never moves")

# A second release on the same session is a no-op.
ob("Mover").location.x = 0.3
bpy.context.view_layer.update()
release()
check(abs(loc(ob("Mover")).x - 0.3) < 1e-6, "commit runs at most once per session")

# One Ctrl+Z reverts the whole grab (native move + snap).
reset()
begin()
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
release()
check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)), "snapped before undo")
bpy.ops.ed.undo()
check(close(loc(ob("Mover")), (4, 0, 0)), f"one undo returns to the start: {tuple(loc(ob('Mover')))}")

# Cancelled transform (back at the start pose): nothing to snap.
reset()
begin()
release()
check(close(loc(ob("Mover")), (4, 0, 0)) and not ov._session.committed, "cancel leaves the pose")

# Released far from every guide: no snap.
reset()
begin()
move(ob("Mover"), by=(-1.0, 1.5, 0.0))
release()
check(close(loc(ob("Mover")), (3.0, 1.5, 0.0)), "no guide in range, no change")
check(not ov._session.committed, "unsnapped release does not commit")

# Approach with drag ticks, as a real drag does (mirrors the live "translate"
# scenario): relationships a move cannot change (edges perpendicular to
# Target's) must not latch at 0 px on the first tick and block the Y alignment.
# The start and end are clear of every on-screen alignment, so nothing but
# those relationships sits at 0 px on the first tick.
reset()
start, end = Vector((2.5, -1.5, 0.0)), Vector((2.4, 4.93, 0.0))
ob("Mover").location = start
bpy.context.view_layer.update()
push("start")
begin()
for k in range(1, 11):
    ob("Mover").location = start.lerp(end, k / 10)
    bpy.context.view_layer.update()
    ov._tick(bpy.context, view=TOP)
push("native move")
release()
check(close(loc(ob("Mover")), (2.4, 5.0, 0.0)),
      f"approach then release snaps Y onto Target: {tuple(loc(ob('Mover')))}")

# ── Translate: which axes may snap ───────────────────────────────────────────
# Native Y lock (G Y): the X correction is masked away.
reset()
begin()
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
ov._session.constraint = (False, True, False)
release()
check(close(loc(ob("Mover")), (0.15, 1.5, 0.0)), "a native axis lock blocks off-axis snaps")

# Native X lock keeps the X correction.
reset()
begin()
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
ov._session.constraint = (True, False, False)
release()
check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)), "a native lock on the snap axis keeps it")

# Unexpected undo stack: the native move pushed no step, so undo lands on an
# older state where Mover is not at its start. The collapse must notice and
# fall back to applying the final pose with a separate step.
reset()
ob("Mover").location = (-5.0, 0.0, 0.0)
bpy.context.view_layer.update()
push("unrelated A")
push("unrelated B")
ob("Mover").matrix_world = START["Mover"].copy()
bpy.context.view_layer.update()
begin()
move(ob("Mover"), by=(-3.85, 1.5, 0.0), record=False)
release()
check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)),
      f"fallback still lands the snapped pose: {tuple(loc(ob('Mover')))}")
check(close(loc(ob("Target")), (0, 5, 0)), "fallback leaves other objects in place")

# Mover lands 0.1 m off Target's Y row. Y is the depth axis of the front view.
for name, view, expect_y in (("top ortho", TOP, 5.0), ("perspective", PERSP, 5.0),
                             ("front ortho", FRONT, 5.1)):
    reset()
    begin(view=view)
    move(ob("Mover"), by=(3.0, 5.1, 0.0))  # (7, 5.1, 0): far from Target on X
    release(view=view)
    check(abs(loc(ob("Mover")).y - expect_y) < 1e-4,
          f"{name}: Y lands at {loc(ob('Mover')).y:.4f}, expected {expect_y}")
    check(abs(loc(ob("Mover")).x - 7.0) < 1e-4, f"{name}: X untouched")

# ── Translate: guards ────────────────────────────────────────────────────────
def guarded(label, setup):
    reset()
    begin()
    move(ob("Mover"), by=(-3.85, 1.5, 0.0))
    setup()
    release()
    check(close(loc(ob("Mover")), (0.15, 1.5, 0.0)), f"no commit when {label}")


guarded("Magnets is off", lambda: setattr(opts(), "enabled", False))
guarded("soft snap is off", lambda: setattr(opts(), "soft_snap", False))
guarded("Blender snapping is on", lambda: setattr(ts(), "use_snap", True))


def _reselect():
    ob("Mover").select_set(False)
    ob("Target").select_set(True)
    bpy.context.view_layer.objects.active = ob("Target")


guarded("the selection changed", _reselect)

reset()
begin()
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
ov._commit_release(bpy.context, view=(None, None))
check(close(loc(ob("Mover")), (0.15, 1.5, 0.0)), "no commit without a viewport")

# ── Translate: multi-object ──────────────────────────────────────────────────
reset(selected=("Mover", "Mover2"))
begin()
check(ov._session.moving_names == {"Mover", "Mover2"}, "both objects are in the session")
move(ob("Mover"), ob("Mover2"), by=(-3.85, 1.5, 0.0))
release()
check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)), f"first object snapped: {tuple(loc(ob('Mover')))}")
check(close(loc(ob("Mover2")), (0.0, -1.5, 0.0)), f"second object moved with it: {tuple(loc(ob('Mover2')))}")

# ── Translate: edit mode ─────────────────────────────────────────────────────
reset()
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(ob("Mover").data)
for v in bm.verts:
    v.select = True
bm.select_flush(True)
bmesh.update_edit_mesh(ob("Mover").data)
begin()
check(ov._session.edit_mode and ov._session.start_matrices is None,
      "edit-mode session tracks vertices, not object poses")
bm = bmesh.from_edit_mesh(ob("Mover").data)
for v in bm.verts:
    v.co += Vector((-3.85, 1.5, 0.0))  # object has no rotation/scale: local == world offset
bmesh.update_edit_mesh(ob("Mover").data)
release()
bm = bmesh.from_edit_mesh(ob("Mover").data)
centroid = sum((ob("Mover").matrix_world @ v.co for v in bm.verts), Vector()) / len(bm.verts)
check(close(centroid, (0.0, 1.5, 0.0)), f"edit-mode snap moves the vertices: {tuple(centroid)}")
check(close(loc(ob("Mover")), (4, 0, 0)), "edit-mode snap leaves the object origin")
for v in bm.verts:  # restore the mesh around the object origin
    v.co -= centroid - Vector((4.0, 0.0, 0.0))
bmesh.update_edit_mesh(ob("Mover").data)
bpy.ops.object.mode_set(mode="OBJECT")

# ── Rotate: angle-increment snap ─────────────────────────────────────────────
def rotated(deg, *, mode="OBJECT"):
    reset()
    begin("TRANSFORM_OT_rotate")
    ob("Mover").rotation_euler.z = math.radians(deg)
    bpy.context.view_layer.update()
    push("native rotate")
    release()
    return math.degrees(ob("Mover").matrix_world.to_euler().z)


check(abs(opts().angle_snap_increment - 15.0) < 1e-6, "default increment is 15 degrees")
angle = rotated(44.0)
check(abs(angle - 45.0) < 1e-3, f"44 deg snaps to 45, got {angle:.3f}")
check(close(loc(ob("Mover")), (4, 0, 0)), "rotation about the object's own origin keeps it in place")
bpy.ops.ed.undo()
check(abs(ob("Mover").matrix_world.to_euler().z) < 1e-6, "one undo reverts the snapped rotate")
angle = rotated(37.0)
check(abs(angle - 37.0) < 1e-3, f"37 deg is a deliberate angle, got {angle:.3f}")
angle = rotated(0.0)
check(abs(angle) < 1e-6 and not ov._session.committed, "cancelled rotate does nothing")
opts().angle_snap_increment = 0.0
angle = rotated(44.0)
check(abs(angle - 44.0) < 1e-3, "increment 0 disables the rotate snap")
opts().property_unset("angle_snap_increment")

# ── Scale: equal-size snap ───────────────────────────────────────────────────
def scaled(factor):
    reset()
    begin("TRANSFORM_OT_resize")
    ob("Mover").scale = (factor, factor, factor)
    bpy.context.view_layer.update()
    push("native resize")
    release()
    return max(ob("Mover").dimensions)


size = scaled(2.95)  # 5.9 m, next to Big's 6 m
check(abs(size - 6.0) < 1e-3, f"5.9 m snaps to Big's 6 m, got {size:.4f}")
check(close(loc(ob("Mover")), (4, 0, 0)), "scale about the object's own origin keeps it in place")
check(ov._session.size_candidates is not None
      and "Mover" not in dict(ov._session.size_candidates),
      "size candidates exclude the moving object")
bpy.ops.ed.undo()
check(abs(max(ob("Mover").dimensions) - 2.0) < 1e-4, "one undo reverts the snapped resize")
size = scaled(1.0)
check(abs(size - 2.0) < 1e-6 and not ov._session.committed, "cancelled scale does nothing")
size = scaled(2.0)  # 4 m: 2 m from Target and Big, out of range
check(abs(size - 4.0) < 1e-4, f"no neighbour of that size, got {size:.4f}")

# Rotate/scale in edit mode are left to Blender.
for op in ("TRANSFORM_OT_rotate", "TRANSFORM_OT_resize"):
    reset()
    bpy.ops.object.mode_set(mode="EDIT")
    begin(op)
    before = [v.co.copy() for v in bmesh.from_edit_mesh(ob("Mover").data).verts]
    release()
    after = [v.co.copy() for v in bmesh.from_edit_mesh(ob("Mover").data).verts]
    check(before == after and not ov._session.committed, f"{op} in edit mode is not snapped")
    bpy.ops.object.mode_set(mode="OBJECT")

# ── Release right after a jump (typed value, fast flick) ─────────────────────
# A drag tick latches a guide; the selection then jumps beyond the guide range
# and is released within the latch's grace frames. The stale latch must not
# decide the commit.
reset()
begin()
move(ob("Mover"), by=(0.1, 0.0, 0.0))  # (4.1, 0, 0): 0.1 m off Mover2's X column
ov._tick(bpy.context, view=TOP)
check(ov._session.snap.active_key is not None, "the tick latches Mover2's X guide")
move(ob("Mover"), by=(-5.1, 1.5, 0.0))  # (-1, 1.5, 0): no guide within range
release()
check(close(loc(ob("Mover")), (-1.0, 1.5, 0.0)),
      f"a stale latch applies no correction: {tuple(loc(ob('Mover')))}")

reset()
begin()
ov._tick(bpy.context, view=TOP)  # at the start pose: exactly on Mover2's X column
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
release()
check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)),
      f"a stale latch does not block the guide at the release: {tuple(loc(ob('Mover')))}")

# ── Drag ticks: guides and the landing preview ───────────────────────────────
reset()
begin()
move(ob("Mover"), by=(-3.85, 1.5, 0.0))
ov._tick(bpy.context, view=TOP)
state = draw._state
check(ov._session.last_anchor is not None, "tick records the anchor it computed")
check(state.active, "an engaged guide is drawn as active")
check(state.guide_items, "guides are drawn")
check(len(state.ghost_points) == 1 and close(state.ghost_points[0], (0, 1.5, 0)),
      f"ghost ring marks the landing point: {state.ghost_points}")
check(len(state.ghost_edges) == 12, "ghost outline of the mover at its landing pose")
check(close(loc(ob("Mover")), (0.15, 1.5, 0.0)), "ticks never move the selection")

# A stationary cursor skips inference.
ov._session.last_infer_s = -1.0
ov._tick(bpy.context, view=TOP)
check(ov._session.last_infer_s == -1.0, "unchanged pose and view skip the recompute")

# Moving again recomputes.
move(ob("Mover"), by=(0.0, 0.5, 0.0))
ov._tick(bpy.context, view=TOP)
check(ov._session.last_infer_s >= 0.0, "a moved selection recomputes")

# Blender snapping on: guides are hidden.
ts().use_snap = True
ov._tick(bpy.context, view=TOP)
check(not state.guide_items and not state.ghost_points, "Blender snapping hides the guides")
check(ov._session.last_anchor is None, "and forces a recompute once it is off")
ts().use_snap = False

# Adding to the selection keeps the session; dropping the mover ends it.
ob("Target").select_set(True)
ov._tick(bpy.context, view=TOP)
check(ov._session is not None, "extending the selection mid-drag keeps the session")
ob("Mover").select_set(False)
bpy.context.view_layer.objects.active = ob("Target")
ov._tick(bpy.context, view=TOP)
check(ov._session is None, "deselecting the mover mid-drag ends the session")

# Rotate / scale ticks preview the snapped pose with a label.
reset()
begin("TRANSFORM_OT_rotate")
ob("Mover").rotation_euler.z = math.radians(44.0)
bpy.context.view_layer.update()
ov._tick(bpy.context, view=TOP)
check(len(state.ghost_edges) == 12, "rotate preview outlines the snapped pose")
check(any("45" in lab[1] for lab in state.labels), f"rotate preview label: {state.labels}")

reset()
begin("TRANSFORM_OT_resize")
ob("Mover").scale = (2.95, 2.95, 2.95)
bpy.context.view_layer.update()
ov._tick(bpy.context, view=TOP)
check(len(state.ghost_edges) == 12, "scale preview outlines the snapped pose")
check(any("Big" in lab[1] for lab in state.labels), f"scale preview label: {state.labels}")

# ── Timer state machine: begin → tick → release → commit → end ───────────────
reset()
running = {"op": "TRANSFORM_OT_translate"}
orig_active, orig_view3d = ov._active_transform_id, ov._view3d_context
ov._active_transform_id = lambda _ctx: running["op"]
ov._view3d_context = lambda _ctx: (None, *TOP)
try:
    interval = ov._timer_callback_inner()
    check(ov._session is not None and interval <= 0.1, "a running transform starts a session")
    move(ob("Mover"), by=(-3.85, 1.5, 0.0))
    ov._timer_callback_inner()
    check(state.ghost_points, "the drag tick draws the preview")

    running["op"] = None  # the user releases
    check(ov._timer_callback_inner() == 0.05, "idle cadence after release")
    check(close(loc(ob("Mover")), (0.0, 1.5, 0.0)), f"first idle frame commits: {tuple(loc(ob('Mover')))}")
    check(ov._session is not None, "session lingers for the grace frames")
    for _ in range(ov._IDLE_GRACE_FRAMES):
        ov._timer_callback_inner()
    check(ov._session is None, "session ends after the grace frames")

    # A new transform on another selection restarts the session.
    reset()
    running["op"] = "TRANSFORM_OT_translate"
    ov._timer_callback_inner()
    first_key = ov._session.key
    ob("Mover").select_set(False)
    ob("Mover2").select_set(True)
    bpy.context.view_layer.objects.active = ob("Mover2")
    ov._timer_callback_inner()
    check(ov._session is None, "a mid-drag selection change ends the session")
    ov._timer_callback_inner()
    check(ov._session is not None and ov._session.key != first_key,
          "the next frame starts a session for the new selection")

    # Magnets switched off: no session.
    reset()
    opts().enabled = False
    ov._timer_callback_inner()
    check(ov._session is None, "no session while Magnets is off")
finally:
    ov._active_transform_id, ov._view3d_context = orig_active, orig_view3d
    reset()

addon_utils.disable("magnets", default_set=True)
if failures:
    print(f"MAGNETS_RELEASE_FAILED {len(failures)}")
else:
    print("MAGNETS_RELEASE_OK")
