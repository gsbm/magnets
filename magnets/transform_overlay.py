"""Overlay guides on Blender native transform (G/R/S).

Native transform owns interaction. Guides are drawn during the drag; the snap
correction is applied once on release as a committed change.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import bmesh
import bpy
from mathutils import Vector

from . import log
from .adapters.bmesh_extract import (
    apply_edit_translation,
    edit_mesh_feature_pool,
)
from .adapters.extract import object_feature_pool
from .adapters.snapshot import InteractionSnapshot
from .core.features import FeaturePool
from .core.session import selection_matches_session
from .core.snap_apply import masked_translation, project_out_direction
from .core.tolerance import SnapHysteresis
from .core.transform import TransformMode
from .core.transform_snap import (
    adaptive_interval,
    equal_size_scale,
    rotated_matrix,
    scaled_matrix,
    snap_rotation_delta,
)
from .draw import handler as draw
from .ops.pipeline import (
    push_guides,
    run_inference,
    world_per_pixel,
)
from .properties import extract_options, get_options

_TRANSFORM_OPS: dict[str, TransformMode] = {
    "TRANSFORM_OT_translate": TransformMode.TRANSLATE,
    "TRANSFORM_OT_rotate": TransformMode.ROTATE,
    "TRANSFORM_OT_resize": TransformMode.SCALE,
    "TRANSFORM_OT_transform": TransformMode.TRANSLATE,
}

_IDLE_GRACE_FRAMES = 3

# Live-transform timer cadence. Avoid 0.0 (ASAP) to limit inference rate.
_ACTIVE_INTERVAL = 1.0 / 120.0

# Fraction of a screen pixel at the anchor depth treated as no movement.
_ANCHOR_MOVE_FRACTION = 0.05


@dataclass
class _Session:
    """Per-interaction state for one native transform.

    Cleared when the transform ends so no session state outlives the drag.
    """

    key: tuple
    op: str
    moving_names: frozenset[str]
    edit_mode: bool
    snapshot: InteractionSnapshot
    world_tol: float | None
    start_anchor: Vector | None
    # Per-object world matrices at session start (object mode only), used to
    # collapse the native transform + snap into a single undo step.
    start_matrices: dict | None
    snap: SnapHysteresis = field(default_factory=SnapHysteresis)
    constraint: tuple | None = None
    committed: bool = False
    idle_frames: int = 0
    # Change detection: anchor + view matrix of the last computed frame, so a
    # stationary cursor skips recompute.
    last_anchor: Vector | None = None
    last_view: object | None = None
    # Wall-clock cost of the last inference tick, feeding the adaptive throttle.
    last_infer_s: float = 0.0


_timer = None
_session: _Session | None = None


def _options(context):
    try:
        return get_options(context)
    except Exception:  # pragma: no cover - scene not ready
        return None


def _selection_valid_for_session(context) -> bool:
    if _session is None:
        return False
    edit_mode = context.mode == "EDIT_MESH"
    selected = frozenset(obj.name for obj in context.selected_objects)
    active = context.active_object.name if context.active_object else None
    return selection_matches_session(
        _session.moving_names,
        _session.edit_mode,
        edit_mode=edit_mode,
        selected_names=selected,
        active_name=active,
    )


def _iter_view3d(context):
    """Yield ``(area, region, rv3d)`` for every 3D viewport across all windows.

    A ``bpy.app.timers`` callback cannot see the mouse, so it cannot know which
    viewport the drag is in. Scanning *all* windows (not just the active one)
    at least makes second-monitor / multi-window layouts work, and lets the
    caller apply a deterministic, frame-stable choice.
    """
    wm = getattr(context, "window_manager", None)
    windows = list(getattr(wm, "windows", []) or [])
    if not windows:
        window = getattr(context, "window", None)
        if window is not None:
            windows = [window]
    for window in windows:
        screen = getattr(window, "screen", None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            rv3d = getattr(space, "region_3d", None)
            if rv3d is None:
                continue
            for region in area.regions:
                if region.type == "WINDOW":
                    yield area, region, rv3d


def _view3d_context(context):
    """Return ``(area, region, rv3d)`` for the largest 3D viewport.

    Inference uses that viewport's zoom for screen-space tolerances. Guides are
    drawn in world space in every View3D via per-region handlers.
    """
    best = (None, None, None)
    best_area = -1
    for area, region, rv3d in _iter_view3d(context):
        size = region.width * region.height
        if size > best_area:
            best_area = size
            best = (area, region, rv3d)
    return best


def _redraw(context):
    for area, _, _ in _iter_view3d(context):
        area.tag_redraw()


def _objects_to_exclude(context) -> list:
    if context.mode == "EDIT_MESH":
        return []
    selected = list(context.selected_objects)
    if selected:
        return selected
    obj = context.active_object
    return [obj] if obj is not None else []


def _moving_objects(context) -> list:
    if context.mode == "EDIT_MESH":
        obj = context.active_object
        return [obj] if obj is not None else []
    selected = list(context.selected_objects)
    if selected:
        return selected
    obj = context.active_object
    return [obj] if obj is not None else []


def _session_key_for(context, op_id: str) -> tuple:
    exclude = _objects_to_exclude(context)
    return (op_id, tuple(sorted(obj.name for obj in exclude)))


def _moving_target(context):
    objs = _moving_objects(context)
    if not objs:
        return None, None, None, False, None

    primary = context.active_object or objs[0]
    edit_mode = context.mode == "EDIT_MESH" and primary.type == "MESH"

    if edit_mode:
        bm = bmesh.from_edit_mesh(primary.data)
        pool = edit_mesh_feature_pool(primary, bm)
        anchor = _selection_centroid(primary, bm)
        return primary, pool, anchor, True, bm

    opts = extract_options(get_options(context))
    pool = FeaturePool()
    anchor = Vector((0.0, 0.0, 0.0))
    for obj in objs:
        pool.extend(object_feature_pool(obj, **opts))
        anchor += obj.matrix_world.translation
    anchor /= len(objs)
    return primary, pool, anchor, False, None


def _selection_centroid(obj, bm):
    mw = obj.matrix_world
    sel = [v for v in bm.verts if v.select]
    if not sel:
        return mw.translation.copy()
    center = Vector((0.0, 0.0, 0.0))
    for v in sel:
        center += v.co
    center /= len(sel)
    return mw @ center


def _cheap_anchor(context) -> Vector | None:
    """Anchor position without extracting the full feature pool.

    Used only for change-detection so a stationary cursor skips inference.
    """
    if context.mode == "EDIT_MESH":
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return None
        bm = bmesh.from_edit_mesh(obj.data)
        return _selection_centroid(obj, bm)
    objs = _moving_objects(context)
    if not objs:
        return None
    anchor = Vector((0.0, 0.0, 0.0))
    for obj in objs:
        anchor += obj.matrix_world.translation
    anchor /= len(objs)
    return anchor


def _begin_session(context, op_id: str):
    global _session

    moving = _moving_objects(context)
    if not moving:
        return

    edit_mode = context.mode == "EDIT_MESH"
    # Snapshot each moving object's start pose so the commit can rebuild the
    # whole move as one undo step (object mode only; edit mode uses bmesh).
    start_matrices = (
        None if edit_mode else {obj.name: obj.matrix_world.copy() for obj in moving}
    )
    opts = extract_options(get_options(context))
    exclude = _objects_to_exclude(context)
    snapshot = InteractionSnapshot.from_context(context, exclude=exclude, **opts)

    world_tol = None
    _area, region, rv3d = _view3d_context(context)
    obj = context.active_object
    if region is not None and rv3d is not None and obj is not None:
        wpp = world_per_pixel(region, rv3d, obj.matrix_world.translation)
        world_tol = get_options(context).passive_range_px * wpp

    _session = _Session(
        key=_session_key_for(context, op_id),
        op=op_id,
        moving_names=frozenset(obj.name for obj in moving),
        edit_mode=edit_mode,
        snapshot=snapshot,
        world_tol=world_tol,
        start_anchor=_cheap_anchor(context),
        start_matrices=start_matrices,
    )

    if log.debug_enabled():
        log.debug(
            f"session begin: op={op_id} moving={sorted(_session.moving_names)} "
            f"candidates={len(snapshot.pool.points)}pts world_tol={world_tol}"
        )
    draw.enable()


def _end_session():
    global _session
    _session = None
    draw.disable()


def _active_transform_id(context) -> str | None:
    """Return the live native transform operator id, or None.

    Prefers ``Window.modal_operators`` (clears when the modal ends) over
    ``context.active_operator`` (lingers after release). Scans all windows;
    falls back to ``active_operator`` if the modal API is unavailable.
    """
    wm = getattr(context, "window_manager", None)
    modal_api_seen = False
    for window in list(getattr(wm, "windows", []) or []):
        modal_ops = getattr(window, "modal_operators", None)
        if modal_ops is None:
            continue
        modal_api_seen = True
        for op in modal_ops:
            bl_idname = getattr(op, "bl_idname", None)
            if bl_idname in _TRANSFORM_OPS:
                return bl_idname
    if modal_api_seen:
        return None
    # Pre-4.1 Blender without Window.modal_operators: best effort. active_operator
    # keeps guides drawing during the drag but cannot mark the release edge.
    op = getattr(context, "active_operator", None)
    bl_idname = getattr(op, "bl_idname", None)
    return bl_idname if bl_idname in _TRANSFORM_OPS else None


def _read_native_constraint(context) -> tuple | None:
    """Global-axis mask of the running transform's lock, or None if free.

    Returns a 3-tuple of booleans for a global ``G X`` / ``G Shift+Z`` style
    lock, else None (free drag, or a non-global orientation we do not restrict).
    Best effort: the native transform's constraint is read from the operator.
    """
    op = getattr(context, "active_operator", None)
    if op is None or getattr(op, "bl_idname", None) not in _TRANSFORM_OPS:
        return None
    try:
        caxis = tuple(bool(v) for v in op.constraint_axis)
        orient = op.orient_type
    except (AttributeError, TypeError):
        return None
    if not any(caxis) or orient not in ("GLOBAL", ""):
        return None
    return caxis


def _snap_correction(translation: Vector, rv3d, native_mask: tuple | None) -> Vector:
    """Constrain a snap correction to axes the selection may move on.

    Priority:
        1. Native axis/plane lock (``G X``, ``G Shift+Z``): those axes only.
        2. Orthographic view: drop the view-normal (depth) axis.
        3. Perspective drag: full 3-axis correction.

    Used by both the drag ghost and the release commit.
    """
    if native_mask is not None:
        return Vector(masked_translation(translation, native_mask))
    if getattr(rv3d, "is_perspective", True):
        return translation.copy()
    view_normal = rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))
    return Vector(project_out_direction(translation, view_normal))


def _tick(context):
    if _session is None:
        return
    options = get_options(context)
    if not options.enabled:
        return

    if not _selection_valid_for_session(context):
        _end_session()
        _redraw(context)
        return

    area, region, rv3d = _view3d_context(context)
    if region is None or rv3d is None:
        return

    # Skip inference when selection pose and view matrix are unchanged.
    probe = _cheap_anchor(context)
    view_mat = rv3d.view_matrix
    if (
        probe is not None
        and _session.last_anchor is not None
        and _session.last_view is not None
    ):
        move_eps = world_per_pixel(region, rv3d, probe) * _ANCHOR_MOVE_FRACTION
        if (
            (probe - _session.last_anchor).length_squared < move_eps * move_eps
            and _session.last_view == view_mat
        ):
            return

    obj, moving, anchor, edit_mode, bm = _moving_target(context)
    if obj is None:
        _end_session()
        _redraw(context)
        return

    _session.last_anchor = anchor.copy()
    _session.last_view = view_mat.copy()

    transform_mode = _TRANSFORM_OPS.get(_session.op, TransformMode.TRANSLATE)
    _t0 = time.perf_counter()
    result = run_inference(
        context,
        region=region,
        rv3d=rv3d,
        snapshot=_session.snapshot,
        moving=moving,
        anchor_world=anchor,
        snap=_session.snap,
        transform_mode=transform_mode,
        frozen_world_tol=_session.world_tol,
    )
    _session.last_infer_s = time.perf_counter() - _t0

    if log.debug_enabled():
        best = result.ranked[0].screen_dist if result.ranked else -1.0
        log.debug(
            f"tick: ranked={len(result.ranked)} snapped={result.snapped} "
            f"best_screen_px={best:.1f} active={len(result.active_set)}"
        )

    # Track the native axis lock (G X, G Shift+Z) so the ghost and the release
    # commit both respect it.
    _session.constraint = _read_native_constraint(context)

    # Ghost: where the selection lands if released now (translate only; for
    # rotate/scale the anchor barely moves, so a ghost point is not meaningful).
    ghost_co = None
    if (
        result.snapped
        and transform_mode == TransformMode.TRANSLATE
        and options.soft_snap
    ):
        corr = _snap_correction(result.translation, rv3d, _session.constraint)
        if corr.length_squared > 1e-12:
            ghost_co = anchor + corr

    push_guides(
        context,
        region=region,
        rv3d=rv3d,
        result=result,
        depth_co=anchor,
        ghost_co=ghost_co,
    )
    _redraw(context)


def _commit_release(context):
    """Apply the engaged snap once, after the native transform is released.

    Dispatches on the transform mode: translate snaps to guides (inference),
    rotate snaps to angle increments, scale snaps to a neighbour's size. All
    three fold into a single undo step in object mode (see ``_commit_collapsed``).
    """
    if _session is None or _session.committed:
        return
    options = _options(context)
    if options is None or not options.enabled or not options.soft_snap:
        log.debug("commit skip: disabled or soft_snap off")
        return
    if not _selection_valid_for_session(context):
        log.debug("commit skip: selection changed")
        return

    _area, region, rv3d = _view3d_context(context)
    if region is None or rv3d is None:
        return

    obj, moving, anchor, edit_mode, bm = _moving_target(context)
    if obj is None:
        return

    mode = _TRANSFORM_OPS.get(_session.op, TransformMode.TRANSLATE)
    if mode == TransformMode.TRANSLATE:
        _commit_translate(context, region, rv3d, obj, moving, anchor, edit_mode, bm)
    elif mode == TransformMode.ROTATE:
        _commit_rotate(context, obj, edit_mode)
    elif mode == TransformMode.SCALE:
        _commit_scale(context, obj, anchor, edit_mode)


def _commit_translate(context, region, rv3d, obj, moving, anchor, edit_mode, bm):
    # Confirm vs cancel: a cancelled transform restores the start position
    # exactly, so an unmoved anchor means "nothing to snap".
    if _session.start_anchor is None:
        return
    if (anchor - _session.start_anchor).length_squared < 1e-9:
        log.debug("commit skip: unmoved (cancelled or zero move)")
        return

    result = run_inference(
        context,
        region=region,
        rv3d=rv3d,
        snapshot=_session.snapshot,
        moving=moving,
        anchor_world=anchor,
        snap=_session.snap,
        transform_mode=TransformMode.TRANSLATE,
        frozen_world_tol=_session.world_tol,
    )
    if not result.snapped:
        best = result.ranked[0].screen_dist if result.ranked else -1.0
        log.debug(
            f"commit skip: not engaged (ranked={len(result.ranked)} "
            f"best_screen_px={best:.1f})"
        )
        return

    # Prefer a fresh read of the finished transform's lock; fall back to the one
    # captured on the last drag frame (active_operator may already be gone).
    native_mask = _read_native_constraint(context)
    if native_mask is None:
        native_mask = _session.constraint
    correction = _snap_correction(result.translation, rv3d, native_mask)
    if correction.length_squared < 1e-12:
        log.debug(f"commit skip: correction ~0 (lock={native_mask})")
        return

    _session.committed = True

    if edit_mode and bm is not None:
        # Edit mode: translate the selected verts and record it. The native
        # edit-mode transform already pushed its own step, so this remains a
        # second undo entry (bmesh state makes an undo-collapse unsafe).
        apply_edit_translation(obj, bm, correction)
        bmesh.update_edit_mesh(obj.data)
        try:
            bpy.ops.ed.undo_push(message="Magnets Snap")
        except (RuntimeError, TypeError):  # pragma: no cover - context dependent
            pass
        log.debug(
            f"commit APPLIED (edit): correction={tuple(round(v, 4) for v in correction)} "
            f"lock={native_mask} axes={[r.axis for r in result.active_set]}"
        )
        _redraw(context)
        return

    # Object mode: fold the native move + snap into ONE undo step so a single
    # Ctrl+Z reverts the whole grab (native + snap), matching Blender's feel.
    poses = {}
    for moving_obj in _moving_objects(context):
        m = moving_obj.matrix_world.copy()
        m.translation = m.translation + correction
        poses[moving_obj.name] = m
    collapsed = _finish_object_commit(context, poses, "Magnets Move")
    log.debug(
        f"commit APPLIED (translate, collapsed={collapsed}): "
        f"correction={tuple(round(v, 4) for v in correction)} "
        f"lock={native_mask} axes={[r.axis for r in result.active_set]}"
    )


def _commit_rotate(context, obj, edit_mode):
    if edit_mode:
        log.debug("commit skip: edit-mode rotate snap not supported")
        return
    if not _session.start_matrices:
        return
    start_m = _session.start_matrices.get(obj.name)
    if start_m is None:
        return

    increment = get_options(context).angle_snap_increment
    snap = snap_rotation_delta(start_m, obj.matrix_world, increment)
    if snap is None:
        log.debug("commit skip: rotation not near a snap increment")
        return
    axis, total_angle = snap
    pivot = _session.start_anchor or start_m.translation.copy()

    poses = {}
    for moving_obj in _moving_objects(context):
        s = _session.start_matrices.get(moving_obj.name)
        if s is None:
            continue
        poses[moving_obj.name] = rotated_matrix(s, axis, total_angle, pivot)
    if not poses:
        return

    collapsed = _finish_object_commit(context, poses, "Magnets Rotate")
    log.debug(
        f"commit APPLIED (rotate, collapsed={collapsed}): "
        f"angle={math.degrees(total_angle):.2f}deg "
        f"axis={tuple(round(a, 3) for a in axis)}"
    )


def _commit_scale(context, obj, anchor, edit_mode):
    if edit_mode:
        log.debug("commit skip: edit-mode scale snap not supported")
        return
    if not _session.start_matrices:
        return
    start_m = _session.start_matrices.get(obj.name)
    if start_m is None:
        return
    tol = _session.world_tol
    if not tol or tol <= 0.0:
        return

    # Confirm vs cancel: a cancelled scale restores the start size exactly, so an
    # unchanged scale means "nothing to snap" (else we'd resize a cancelled edit
    # just because a neighbour happened to be within tolerance).
    start_scale = start_m.to_scale()
    if (obj.matrix_world.to_scale() - start_scale).length < 1e-6 * (
        1.0 + start_scale.length
    ):
        log.debug("commit skip: scale unchanged (cancelled or zero scale)")
        return

    dims = obj.dimensions
    current_dim = max(dims) if len(dims) else 0.0
    candidates = _nearby_dimensions(context, anchor, _session.moving_names)
    factor = equal_size_scale(current_dim, candidates, tol)
    if factor is None:
        log.debug("commit skip: size not near a neighbour")
        return
    pivot = _session.start_anchor or obj.matrix_world.translation.copy()

    # Scale factor is relative to the *current* (post-native-scale) size, so
    # build finals from the live matrices; the collapse re-applies them as
    # absolute poses regardless of the undo reset.
    poses = {
        moving_obj.name: scaled_matrix(moving_obj.matrix_world, factor, pivot)
        for moving_obj in _moving_objects(context)
    }
    collapsed = _finish_object_commit(context, poses, "Magnets Resize")
    log.debug(
        f"commit APPLIED (scale, collapsed={collapsed}): "
        f"factor={factor:.4f} target_dim={current_dim * factor:.4f}"
    )


def _nearby_dimensions(context, anchor: Vector, exclude_names) -> list[float]:
    """Overall sizes (largest bbox dimension) of non-moving scene objects.

    Runs once per commit, not per frame, so a full scan is fine.
    """
    del anchor  # full scan; kept for signature symmetry with the callers
    exclude = set(exclude_names or ())
    out: list[float] = []
    for other in context.view_layer.objects:
        if other.name in exclude:
            continue
        d = other.dimensions
        biggest = max(d) if len(d) else 0.0
        if biggest > 1e-9:
            out.append(biggest)
    return out


def _apply_final_poses(poses: dict) -> None:
    """Write each object's final world matrix (scale/rotation encoded in it)."""
    for name, matrix in poses.items():
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.matrix_world = matrix.copy()


def _finish_object_commit(context, poses: dict, label: str) -> bool:
    """Apply final object-mode poses, preferring a single undo step.

    Tries ``_commit_collapsed``; on failure applies poses and pushes a separate
    undo step.
    """
    _session.committed = True
    start_matrices = _session.start_matrices
    if _commit_collapsed(context, poses, label, start_matrices):
        _redraw(context)
        return True
    _apply_final_poses(poses)
    try:
        bpy.ops.ed.undo_push(message=label)
    except (RuntimeError, TypeError):  # pragma: no cover - context dependent
        pass
    _redraw(context)
    return False


def _returned_to_start(start_matrices: dict) -> bool:
    """True if every moving object is back at its session-start pose.

    Called right after ``ed.undo()`` to confirm the step we removed really was
    the native transform (and not something else that slipped onto the stack),
    scaled to the scene so it holds for millimetre and kilometre work alike.
    """
    if not start_matrices:
        return False
    for name, start_mw in start_matrices.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            return False
        start_t = start_mw.translation
        eps = 1e-4 * (1.0 + start_t.length)
        if (obj.matrix_world.translation - start_t).length > eps:
            return False
    return True


def _commit_collapsed(context, poses: dict, label: str, start_matrices: dict) -> bool:
    """Undo the native transform and re-apply the snapped pose as one step.

    Returns True on success. Any failure (restricted timer context, an
    unexpected undo stack) leaves the collapse un-done and returns False so the
    caller falls back to a plain, always-safe second undo push.
    """
    if not start_matrices:
        return False
    try:
        bpy.ops.ed.undo()
    except (RuntimeError, TypeError):  # pragma: no cover - context dependent
        return False
    if not _returned_to_start(start_matrices):
        # We popped something other than the native transform; do not compound
        # it. Applying finals below still lands the correct final pose.
        log.debug("commit collapse: post-undo pose mismatch, using fallback")
        return False
    _apply_final_poses(poses)
    try:
        bpy.ops.ed.undo_push(message=label)
    except (RuntimeError, TypeError):  # pragma: no cover - context dependent
        return False
    return True


# Timer callbacks that raise are unregistered by Blender. Catch, log with a
# bound, reset session state, and keep the timer armed. After repeated failures
# back off, then resume on the next clean tick.
_consec_failures = 0
_errors_logged = 0
_MAX_CONSEC_FAILURES = 8
_MAX_ERRORS_LOGGED = 5
_FAILURE_COOLDOWN = 2.0


def _failure_interval(consec_failures: int) -> float:
    """Return timer delay after a failed tick."""
    if consec_failures >= _MAX_CONSEC_FAILURES:
        return _FAILURE_COOLDOWN
    return 0.1


def _timer_callback():
    """Timer entry that isolates exceptions from Blender's timer registry."""
    global _consec_failures, _errors_logged
    try:
        interval = _timer_callback_inner()
        _consec_failures = 0
        return interval
    except Exception:
        _consec_failures += 1
        if _errors_logged < _MAX_ERRORS_LOGGED:
            _errors_logged += 1
            log.exception("timer error (overlay kept alive)")
        # Reset session state so the next tick starts clean; hide any stale draw.
        try:
            _end_session()
        except Exception:
            pass
        if _consec_failures == _MAX_CONSEC_FAILURES:
            log.warning(
                "repeated timer errors; overlay paused to a slow heartbeat; "
                "it resumes automatically once the error clears"
            )
        return _failure_interval(_consec_failures)


def _timer_callback_inner():
    context = bpy.context
    if context is None:
        return 0.1

    options = _options(context)
    enabled = bool(options and options.enabled)
    op_id = _active_transform_id(context)

    if op_id is not None and enabled:
        if _session is not None:
            _session.idle_frames = 0
        if _session is None:
            _begin_session(context, op_id)
        elif not _selection_valid_for_session(context):
            _end_session()
            _redraw(context)
            return 0.0
        elif _session.key != _session_key_for(context, op_id):
            _begin_session(context, op_id)
        if _session is not None:
            _tick(context)
        # Slow the timer when inference cost exceeds the adaptive budget.
        last_infer_s = _session.last_infer_s if _session is not None else 0.0
        return adaptive_interval(last_infer_s, base=_ACTIVE_INTERVAL)

    if _session is not None:
        if not _selection_valid_for_session(context):
            _end_session()
            _redraw(context)
        else:
            _session.idle_frames += 1
            if _session.idle_frames == 1:
                # First confirmed frame after the transform ended: commit snap.
                _commit_release(context)
            if _session is not None and _session.idle_frames >= _IDLE_GRACE_FRAMES:
                _end_session()
                _redraw(context)

    return 0.05


def register():
    """Register Blender classes / handlers for this module."""
    global _timer
    if _timer is not None:
        return
    _timer = bpy.app.timers.register(_timer_callback, persistent=True)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    global _timer
    _end_session()
    if _timer is not None:
        bpy.app.timers.unregister(_timer)
        _timer = None
