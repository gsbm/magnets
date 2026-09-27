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
from .adapters import scene_cache
from .adapters.bmesh_extract import (
    EditSelection,
    apply_edit_translation,
)
from .adapters.extract import object_feature_pool
from .adapters.snapshot import InteractionSnapshot
from .adapters.units import length_formatter
from .adapters.view import ui_scale
from .core.bbox import bbox_edges, from_blender_bound_box
from .core.features import FeaturePool
from .core.labels import format_length, rotation_snap_label, size_match_label
from .core.session import native_snap_in_effect, selection_matches_session
from .core.snap_apply import masked_translation, project_out_direction
from .core.tolerance import SnapHysteresis
from .core.transform import TransformMode
from .core.transform_snap import (
    adaptive_interval,
    nearest_size_match,
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

# Landing-preview outlines are drawn for at most this many objects.
_GHOST_MAX_OBJECTS = 16


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
    # Edit Mode: the selection captured once at session start, so ticks never
    # rescan the whole mesh.
    edit_selection: EditSelection | None = None
    snap: SnapHysteresis = field(default_factory=SnapHysteresis)
    constraint: tuple | None = None
    committed: bool = False
    idle_frames: int = 0
    # Change detection: anchor + view matrix of the last computed frame, so a
    # stationary cursor skips recompute.
    last_anchor: Vector | None = None
    last_view: object | None = None
    # Active object's matrix on the last computed frame: rotate/scale change
    # it without moving the anchor.
    last_matrix: object | None = None
    # (name, size) of non-moving objects, gathered once for the scale snap.
    size_candidates: list | None = None
    # Wall-clock cost of the last inference tick, feeding the adaptive throttle.
    last_infer_s: float = 0.0


_timer = None
_session: _Session | None = None


def _options(context):
    try:
        return get_options(context)
    except Exception:  # noqa: BLE001 - scene not ready
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
    """Yield ``(area, region, rv3d)`` for every 3D viewport in every window.

    A timer cannot see the mouse, so it cannot tell which viewport the drag is
    in; scanning all windows supports multi-window layouts.
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


def _resolve_view(context, view):
    """Return ``(region, rv3d)``: ``view`` when given, else the largest viewport.

    Passing ``view`` lets a caller without a window (headless tests) drive the
    session, tick and commit with its own region and view.
    """
    if view is not None:
        return view
    _area, region, rv3d = _view3d_context(context)
    return region, rv3d


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
        sel = _edit_selection(primary)
        try:
            pool, anchor = sel.feature_pool(), sel.centroid_world()
        except ReferenceError:  # edit mesh rebuilt mid-session: recapture
            sel = _edit_selection(primary, fresh=True)
            pool, anchor = sel.feature_pool(), sel.centroid_world()
        return primary, pool, anchor, True, sel.bm

    opts = extract_options(get_options(context))
    pool = FeaturePool()
    anchor = Vector((0.0, 0.0, 0.0))
    for obj in objs:
        pool.extend(object_feature_pool(obj, **opts))
        anchor += obj.matrix_world.translation
    anchor /= len(objs)
    return primary, pool, anchor, False, None


def _edit_selection(obj, *, fresh: bool = False) -> EditSelection:
    """Return the session's Edit Mode selection, capturing it on first use."""
    sel = _session.edit_selection if _session is not None else None
    if fresh or sel is None or sel.obj != obj:
        sel = EditSelection(obj, bmesh.from_edit_mesh(obj.data))
        if _session is not None:
            _session.edit_selection = sel
    return sel


def _cheap_anchor(context) -> Vector | None:
    """Anchor position without extracting the full feature pool.

    Used only for change-detection so a stationary cursor skips inference.
    """
    if context.mode == "EDIT_MESH":
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return None
        try:
            return _edit_selection(obj).centroid_world()
        except ReferenceError:
            return _edit_selection(obj, fresh=True).centroid_world()
    objs = _moving_objects(context)
    if not objs:
        return None
    anchor = Vector((0.0, 0.0, 0.0))
    for obj in objs:
        anchor += obj.matrix_world.translation
    anchor /= len(objs)
    return anchor


def _begin_session(context, op_id: str, view=None):
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
    options = get_options(context)
    exclude = _objects_to_exclude(context)
    snapshot = InteractionSnapshot.from_context(
        context,
        exclude=exclude,
        surfaces=options.enable_tangency,
        **extract_options(options),
    )

    world_tol = None
    region, rv3d = _resolve_view(context, view)
    obj = context.active_object
    if region is not None and rv3d is not None and obj is not None:
        wpp = world_per_pixel(region, rv3d, obj.matrix_world.translation)
        world_tol = get_options(context).passive_range_px * ui_scale(context) * wpp

    # Edit Mode: capture the selection now (the one full mesh scan per drag).
    # Always fresh: a previous session's capture may be of another selection.
    edit_selection = None
    if edit_mode and obj is not None and obj.type == "MESH":
        edit_selection = EditSelection(obj, bmesh.from_edit_mesh(obj.data))
    start_anchor = (
        edit_selection.centroid_world()
        if edit_selection is not None
        else _cheap_anchor(context)
    )

    _session = _Session(
        key=_session_key_for(context, op_id),
        op=op_id,
        moving_names=frozenset(obj.name for obj in moving),
        edit_mode=edit_mode,
        snapshot=snapshot,
        world_tol=world_tol,
        start_anchor=start_anchor,
        start_matrices=start_matrices,
        edit_selection=edit_selection,
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


def _op_prop(op, name: str):
    """Read a property of a (C-defined) operator instance, or None.

    Native operators expose their settings on ``op.properties``; direct
    attribute access only works for Python-defined operators.
    """
    props = getattr(op, "properties", None)
    for source in (props, op):
        if source is None:
            continue
        try:
            return getattr(source, name)
        except AttributeError:
            continue
    return None


def _finished_transform(context):
    """Return the just-finished native transform operator, or None."""
    op = getattr(context, "active_operator", None)
    if op is None or getattr(op, "bl_idname", None) not in _TRANSFORM_OPS:
        return None
    return op


def _yield_to_native_snap(context, options, *, finished: bool) -> bool:
    """Return True when Magnets should stand aside for Blender's own snapping.

    Mid-drag only the scene toggle is visible (a timer cannot see a held Ctrl).
    At release the operator's saved ``snap`` flag also records a Ctrl toggle.
    """
    if not getattr(options, "defer_to_native_snap", True):
        return False
    tool_settings = getattr(context.scene, "tool_settings", None)
    tool_use_snap = bool(getattr(tool_settings, "use_snap", False))
    op_snap = None
    if finished:
        op = _finished_transform(context)
        if op is not None:
            op_snap = _op_prop(op, "snap")
    return native_snap_in_effect(tool_use_snap, op_snap)


def _read_native_constraint(context) -> tuple | None:
    """Return the global-axis mask of the running transform's lock, or None.

    A 3-tuple of booleans for a global ``G X`` / ``G Shift+Z`` lock; None for a
    free drag or a non-global orientation.
    """
    op = _finished_transform(context)
    if op is None:
        return None
    caxis = _op_prop(op, "constraint_axis")
    orient = _op_prop(op, "orient_type")
    try:
        caxis = tuple(bool(v) for v in caxis)
    except TypeError:
        return None
    if not any(caxis) or orient not in ("GLOBAL", ""):
        return None
    return caxis


def _snap_correction(translation: Vector, rv3d, native_mask: tuple | None) -> Vector:
    """Constrain a snap correction to the axes the selection may move on.

    A native axis/plane lock wins; otherwise orthographic views drop the depth
    axis and perspective views keep all three. Shared by preview and commit.
    """
    if native_mask is not None:
        return Vector(masked_translation(translation, native_mask))
    if getattr(rv3d, "is_perspective", True):
        return translation.copy()
    view_normal = rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))
    return Vector(project_out_direction(translation, view_normal))


def _tick(context, view=None):
    if _session is None:
        return
    options = get_options(context)
    if not options.enabled:
        return

    if not _selection_valid_for_session(context):
        _end_session()
        _redraw(context)
        return

    if _yield_to_native_snap(context, options, finished=False):
        # Blender's snapping owns this drag: show nothing we will not apply.
        draw.clear_state()
        _session.last_anchor = None
        _redraw(context)
        return

    region, rv3d = _resolve_view(context, view)
    if region is None or rv3d is None:
        return

    # Skip inference when selection pose and view matrix are unchanged.
    probe = _cheap_anchor(context)
    view_mat = rv3d.view_matrix
    primary = context.active_object
    primary_m = (
        primary.matrix_world
        if primary is not None and not _session.edit_mode
        else None
    )
    if (
        probe is not None
        and _session.last_anchor is not None
        and _session.last_view is not None
    ):
        move_eps = world_per_pixel(region, rv3d, probe) * _ANCHOR_MOVE_FRACTION
        if (
            (probe - _session.last_anchor).length_squared < move_eps * move_eps
            and _session.last_view == view_mat
            and (primary_m is None or _session.last_matrix == primary_m)
        ):
            return

    obj, moving, anchor, edit_mode, _bm = _moving_target(context)
    if obj is None:
        _end_session()
        _redraw(context)
        return

    _session.last_anchor = anchor.copy()
    _session.last_view = view_mat.copy()
    _session.last_matrix = primary_m.copy() if primary_m is not None else None

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

    # Landing preview: show where a release would put the selection, using the
    # same helpers as the commit so the preview and the result always agree.
    ghost_co = None
    ghost_poses: dict = {}
    preview_labels: list = []
    if options.soft_snap and transform_mode == TransformMode.TRANSLATE:
        if result.snapped:
            corr = _snap_correction(result.translation, rv3d, _session.constraint)
            if corr.length_squared > 1e-12:
                ghost_co = anchor + corr
                if not edit_mode:
                    ghost_poses = _translate_poses(context, corr)
    elif options.soft_snap and transform_mode == TransformMode.ROTATE:
        rot = _rotate_snap(context, obj, edit_mode)
        if rot is not None:
            axis, angle, pivot = rot
            ghost_poses = _rotate_poses(context, axis, angle, pivot)
            preview_labels.append((pivot, rotation_snap_label(angle)))
    elif options.soft_snap and transform_mode == TransformMode.SCALE:
        match = _scale_snap(context, obj, edit_mode)
        if match is not None:
            factor, name, size, pivot = match
            ghost_poses = _scale_poses(context, factor, pivot)
            size_text = format_length(size, fmt=length_formatter(context))
            preview_labels.append((pivot, size_match_label(name, size_text)))

    push_guides(
        context,
        region=region,
        rv3d=rv3d,
        result=result,
        depth_co=anchor,
        ghost_co=ghost_co,
        ghost_edges=_pose_edges(ghost_poses),
        preview_labels=preview_labels,
    )
    _redraw(context)


def _translate_poses(context, correction: Vector) -> dict:
    """Return final world matrices of the moving objects shifted by ``correction``."""
    poses = {}
    for moving_obj in _moving_objects(context):
        m = moving_obj.matrix_world.copy()
        m.translation = m.translation + correction
        poses[moving_obj.name] = m
    return poses


def _rotate_snap(context, obj, edit_mode: bool):
    """``(axis, angle, pivot)`` a release would rotate to, or None.

    Object mode only. The angle is the net rotation from the session start,
    snapped to the Angle Snap increment (see ``snap_rotation_delta``).
    """
    if edit_mode or not _session.start_matrices:
        return None
    start_m = _session.start_matrices.get(obj.name)
    if start_m is None:
        return None
    increment = get_options(context).angle_snap_increment
    snap = snap_rotation_delta(start_m, obj.matrix_world, increment)
    if snap is None:
        return None
    axis, angle = snap
    pivot = _session.start_anchor or start_m.translation.copy()
    return axis, angle, pivot


def _rotate_poses(context, axis: Vector, angle: float, pivot: Vector) -> dict:
    """Return final world matrices for a snapped rotation of the moving objects."""
    poses = {}
    for moving_obj in _moving_objects(context):
        start = _session.start_matrices.get(moving_obj.name)
        if start is not None:
            poses[moving_obj.name] = rotated_matrix(start, axis, angle, pivot)
    return poses


def _scale_snap(context, obj, edit_mode: bool):
    """``(factor, name, size, pivot)`` a release would scale to, or None.

    Matches the active object's overall size to the nearest non-moving
    object's within the session tolerance. Object mode only.
    """
    if edit_mode or not _session.start_matrices:
        return None
    start_m = _session.start_matrices.get(obj.name)
    if start_m is None:
        return None
    tol = _session.world_tol
    if not tol or tol <= 0.0:
        return None

    # A cancelled scale restores the start size exactly: nothing to snap.
    start_scale = start_m.to_scale()
    if (obj.matrix_world.to_scale() - start_scale).length < 1e-6 * (
        1.0 + start_scale.length
    ):
        return None

    if _session.size_candidates is None:
        _session.size_candidates = _nearby_dimensions(context, _session.moving_names)
    dims = obj.dimensions
    current_dim = max(dims) if len(dims) else 0.0
    match = nearest_size_match(current_dim, _session.size_candidates, tol)
    if match is None:
        return None
    name, size, factor = match
    pivot = _session.start_anchor or obj.matrix_world.translation.copy()
    return factor, name, size, pivot


def _scale_poses(context, factor: float, pivot: Vector) -> dict:
    """Return final world matrices for a snapped uniform scale of the selection.

    The factor is relative to the *current* (post-native-scale) size, so the
    poses are built from the live matrices.
    """
    return {
        moving_obj.name: scaled_matrix(moving_obj.matrix_world, factor, pivot)
        for moving_obj in _moving_objects(context)
    }


def _pose_edges(poses: dict) -> list:
    """Bounding-box outline edges of each object placed at its final pose."""
    edges: list = []
    for name, matrix in list(poses.items())[:_GHOST_MAX_OBJECTS]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        corners = [matrix @ Vector(corner) for corner in obj.bound_box]
        edges.extend(bbox_edges(from_blender_bound_box(corners)))
    return edges


def _commit_release(context, view=None):
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
    if _yield_to_native_snap(context, options, finished=True):
        log.debug("commit skip: Blender snapping is active")
        return
    if not _selection_valid_for_session(context):
        log.debug("commit skip: selection changed")
        return

    region, rv3d = _resolve_view(context, view)
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
        _commit_scale(context, obj, edit_mode)


def _commit_translate(context, region, rv3d, obj, moving, anchor, edit_mode, bm):
    # A cancelled transform restores the start position exactly: nothing to snap.
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
        sel = _session.edit_selection
        apply_edit_translation(
            obj, bm, correction, verts=sel.verts if sel is not None else None
        )
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
    poses = _translate_poses(context, correction)
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
    rot = _rotate_snap(context, obj, edit_mode)
    if rot is None:
        log.debug("commit skip: rotation not near a snap increment")
        return
    axis, total_angle, pivot = rot
    poses = _rotate_poses(context, axis, total_angle, pivot)
    if not poses:
        return

    collapsed = _finish_object_commit(context, poses, "Magnets Rotate")
    log.debug(
        f"commit APPLIED (rotate, collapsed={collapsed}): "
        f"angle={math.degrees(total_angle):.2f}deg "
        f"axis={tuple(round(a, 3) for a in axis)}"
    )


def _commit_scale(context, obj, edit_mode):
    if edit_mode:
        log.debug("commit skip: edit-mode scale snap not supported")
        return
    match = _scale_snap(context, obj, edit_mode)
    if match is None:
        log.debug("commit skip: scale unchanged or size not near a neighbour")
        return
    factor, name, size, pivot = match
    collapsed = _finish_object_commit(
        context, _scale_poses(context, factor, pivot), "Magnets Resize"
    )
    log.debug(
        f"commit APPLIED (scale, collapsed={collapsed}): "
        f"factor={factor:.4f} matched={name!r} size={size:.4f}"
    )


def _nearby_dimensions(context, exclude_names) -> list[tuple[str, float]]:
    """``(name, size)`` of non-moving scene objects (size = largest bbox dim).

    Gathered once per session (cached on it), so a full scan is fine.
    """
    exclude = set(exclude_names or ())
    out: list[tuple[str, float]] = []
    for other in context.view_layer.objects:
        if other.name in exclude:
            continue
        d = other.dimensions
        biggest = max(d) if len(d) else 0.0
        if biggest > 1e-9:
            out.append((other.name, biggest))
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
    """Return True if every moving object is back at its session-start pose.

    Confirms that ``ed.undo()`` removed the native transform step. The
    tolerance scales with the scene.
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
    except Exception:  # noqa: BLE001 - a raising timer is unregistered
        _consec_failures += 1
        if _errors_logged < _MAX_ERRORS_LOGGED:
            _errors_logged += 1
            log.exception("timer error (overlay kept alive)")
        # Reset session state so the next tick starts clean; hide any stale draw.
        try:
            _end_session()
        except Exception:  # noqa: BLE001, S110 - best-effort teardown
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
    scene_cache.register()
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
    scene_cache.unregister()
