"""Blender-side script for ``test_guide_noise_headless.py``.

Drags a cube through busy scenes in top, front, right and perspective views and
checks, frame by frame, what the overlay hands the renderer: how many guides,
which ones, labels, dots, duplicate strokes, and that it all clears on release.

Usage: blender --background --factory-startup --python <this> -- <repo root>
"""

import math
import random
import sys
from pathlib import Path

REPO_ROOT = sys.argv[sys.argv.index("--") + 1]
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import addon_utils
import bpy
from mathutils import Vector

addon_utils.enable("magnets", default_set=True)

from fake_view import FRONT, PERSP, RIGHT, TOP

from magnets import transform_overlay as ov
from magnets.core.guide_draw import segment_key
from magnets.core.relationship import GuideCircle, GuideLine, GuidePlane, GuideSegment
from magnets.draw import handler as draw
from magnets.ops.pipeline import rank_key
from magnets.properties import get_options

failures: list[str] = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        if len(failures) <= 40:
            print(f"CHECK FAILED: {msg}", flush=True)


# Depth axis (world) of each orthographic view; None for perspective.
VIEWS = {
    "top": (TOP, Vector((0.0, 0.0, 1.0))),
    "front": (FRONT, Vector((0.0, 1.0, 0.0))),
    "right": (RIGHT, Vector((1.0, 0.0, 0.0))),
    "persp": (PERSP, None),
}
AXIS_OF = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}
PARALLEL = 0.85  # |cos| above this counts as pointing into the screen


# ── Scenes ───────────────────────────────────────────────────────────────────
def clear_scene():
    ov._end_session()
    draw.clear_state()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def add_mover():
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-6.0, -6.0, 0.0))
    mover = bpy.context.active_object
    mover.name = "Mover"
    bpy.ops.object.select_all(action="DESELECT")
    mover.select_set(True)
    bpy.context.view_layer.objects.active = mover
    bpy.context.view_layer.update()
    return mover


def grid_scene():
    """Same-size cubes on a regular grid, all at the same height."""
    clear_scene()
    for i in range(-2, 3):
        for j in range(-2, 3):
            if (i, j) != (0, 0):
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(i * 2.5, j * 2.5, 0.0))
    return add_mover()


def mixed_scene():
    """Rotated cubes of mixed sizes, cylinders, spheres and empties at mixed heights."""
    clear_scene()
    rng = random.Random(1)
    for k in range(20):
        loc = (rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(-1.5, 1.5))
        kind = k % 4
        if kind == 0:
            bpy.ops.mesh.primitive_cube_add(
                size=rng.uniform(0.5, 2.0), location=loc, rotation=(0, 0, rng.uniform(0, 1))
            )
        elif kind == 1:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=loc)
        elif kind == 2:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=loc)
        else:
            bpy.ops.object.empty_add(location=loc)
    return add_mover()


STEPS = 40


def drag_path(steps=STEPS):
    """Diagonal sweep with a wobble on every axis, crossing the whole scene."""
    for step in range(steps):
        t = step / (steps - 1)
        yield Vector((
            -6.0 + 12.0 * t,
            -6.0 + 11.7 * t + 0.3 * math.sin(t * 20.0),
            0.4 * math.sin(t * 13.0),
        ))


# ── Capture what the overlay pushes to the renderer ──────────────────────────
frames: list = []
_orig_push = ov.push_guides


def _recording_push(context, **kwargs):
    _orig_push(context, **kwargs)
    frames.append(kwargs["result"])


ov.push_guides = _recording_push


def check_frame(label, result, view_normal, opts):
    ranked = result.ranked
    state = draw._state
    tag = f"{label}: "

    # Guide budget: at most max_guides, one per (family, axis) snap slot.
    check(len(ranked) <= opts.max_guides, tag + f"{len(ranked)} guides > {opts.max_guides}")
    slots = [(it.payload.family, it.payload.axis) for it in ranked]
    check(len(set(slots)) == len(slots), tag + f"duplicate slots {slots}")

    # A move cannot change size or edge directions: those markers would sit
    # at 0 px, hold the latch and block real snaps.
    for it in ranked:
        check(it.payload.family not in ("equal_size", "perpendicular"),
              tag + f"{it.payload.family} guide shown during a move")

    # Orthographic views: nothing that points into the screen.
    if view_normal is not None:
        for it in ranked:
            rel = it.payload
            cdir = rel.constraint_dir
            if cdir is not None:
                check(abs(cdir.normalized().dot(view_normal)) < PARALLEL,
                      tag + f"{rel.family} {rel.axis} snaps along the depth axis")
            if rel.family == "alignment":
                check(abs(AXIS_OF[rel.axis].dot(view_normal)) < PARALLEL,
                      tag + f"depth-axis alignment {rel.axis} shown")
            guide = rel.guide
            if isinstance(guide, GuideLine):
                check(abs(guide.direction.normalized().dot(view_normal)) < PARALLEL,
                      tag + f"{rel.family} guide line seen end-on")
            if isinstance(guide, GuideCircle):
                check(abs(guide.normal.normalized().dot(view_normal)) >= 1.0 - PARALLEL,
                      tag + "circle guide seen edge-on")
            if isinstance(guide, GuidePlane):
                check(abs(guide.normal.normalized().dot(view_normal)) < PARALLEL,
                      tag + "plane guide facing the viewer")

    # Engaged state and its decorations.
    active_keys = {rank_key(r) for r in result.active_set} if result.snapped else set()
    engaged = [it for it in ranked if it.key in active_keys]
    engaged_lines = [
        it for it in engaged if isinstance(it.payload.guide, (GuideLine, GuideSegment))
    ]
    check(len(state.labels) == len(engaged),
          tag + f"{len(state.labels)} labels for {len(engaged)} engaged guides")
    check(len(state.snap_dots) <= len(engaged), tag + "more snap dots than engaged guides")
    max_x = len(engaged_lines) * (len(engaged_lines) - 1) // 2
    check(len(state.intersection_dots) <= max_x,
          tag + f"{len(state.intersection_dots)} intersection dots for "
          f"{len(engaged_lines)} engaged lines")
    check(len(state.ghost_points) <= 1, tag + "more than one landing marker")
    check(bool(state.active) == bool(engaged),
          tag + "active flag disagrees with the engaged guides")

    # Strokes: no identical duplicates, finite, and a sane total.
    keys = [segment_key(i.a, i.b, 1e-5) for i in state.guide_items]
    check(len(set(keys)) == len(keys),
          tag + f"{len(keys) - len(set(keys))} duplicate strokes")
    check(all(math.isfinite(c) for i in state.guide_items for c in (*i.a, *i.b)),
          tag + "non-finite guide coordinates")
    check(len(state.guide_items) <= 64, tag + f"{len(state.guide_items)} strokes")
    line_guides = sum(isinstance(it.payload.guide, GuideLine) for it in ranked)
    check(len(state.tick_items) <= 4 * line_guides, tag + "ticks without line guides")


def run_drag(scene_name, build, view_name):
    view, view_normal = VIEWS[view_name]
    opts = get_options(bpy.context)
    mover = build()
    ov._begin_session(bpy.context, "TRANSFORM_OT_translate", view=view)
    frames.clear()
    snapped = 0
    for i, co in enumerate(drag_path()):
        mover.location = co
        bpy.context.view_layer.update()
        ov._tick(bpy.context, view=view)
        if frames:
            check_frame(f"{scene_name}/{view_name} step {i}", frames[-1], view_normal, opts)
            snapped += bool(frames[-1].snapped)
            frames.clear()
    return snapped


# ── Every scene × view ───────────────────────────────────────────────────────
engaged_counts = {}
for scene_name, build in (("grid", grid_scene), ("mixed", mixed_scene)):
    for view_name in VIEWS:
        engaged_counts[(scene_name, view_name)] = run_drag(scene_name, build, view_name)
print(f"engaged frames per {STEPS}:", engaged_counts, flush=True)

# Filtering must not starve snapping: the grid sweep crosses a column or row
# every few steps in every view.
for (scene_name, view_name), n in engaged_counts.items():
    if scene_name == "grid":
        check(n >= STEPS // 10, f"grid/{view_name}: only {n}/{STEPS} frames engaged")

# Passive guides off: only engaged guides are drawn.
opts = get_options(bpy.context)
opts.show_passive_guides = False
mover = grid_scene()
ov._begin_session(bpy.context, "TRANSFORM_OT_translate", view=TOP)
for co in drag_path():
    mover.location = co
    bpy.context.view_layer.update()
    ov._tick(bpy.context, view=TOP)
    check(all(i.active for i in draw._state.guide_items),
          "passive guides drawn although Show Passive Guides is off")
opts.show_passive_guides = True
frames.clear()

# ── Release: the overlay clears at once, not after the grace frames ──────────
mover = grid_scene()
running = {"op": "TRANSFORM_OT_translate"}
orig_active, orig_view3d = ov._active_transform_id, ov._view3d_context
ov._active_transform_id = lambda _ctx: running["op"]
ov._view3d_context = lambda _ctx: (None, *TOP)
try:
    ov._timer_callback_inner()
    mover.location = (0.1, 0.05, 0.0)  # next to the grid centre: guides engage
    bpy.context.view_layer.update()
    ov._timer_callback_inner()
    check(draw._state.guide_items and draw._state.ghost_points, "guides shown while dragging")
    running["op"] = None
    ov._timer_callback_inner()  # release: commit frame
    state = draw._state
    check(not state.guide_items and not state.ghost_points and not state.labels
          and not state.snap_dots and not state.ghost_edges,
          "overlay cleared on the release frame")
    check(ov._session is not None, "session still in its grace frames")
    for _ in range(ov._IDLE_GRACE_FRAMES):
        ov._timer_callback_inner()
        check(not draw._state.guide_items, "nothing redrawn during the grace frames")
    check(ov._session is None, "session ended after the grace frames")
finally:
    ov._active_transform_id, ov._view3d_context = orig_active, orig_view3d
    ov.push_guides = _orig_push

addon_utils.disable("magnets", default_set=True)
if failures:
    print(f"MAGNETS_NOISE_FAILED {len(failures)}")
else:
    print("MAGNETS_NOISE_OK")
