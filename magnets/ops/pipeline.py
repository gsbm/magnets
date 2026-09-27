"""Shared modal inference pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from bpy_extras import view3d_utils
from mathutils import Vector

from ..adapters.frames import frame_axes
from ..adapters.surface import append_surfaces, surface_features_for_point
from ..adapters.units import length_formatter, scene_unit_info
from ..adapters.view import filter_for_view, ui_scale
from ..core import scoring
from ..core import solvers as _solvers  # noqa: F401 - register solver table
from ..core.features import Feature, FeaturePool, feature_anchor
from ..core.graph import build_active_set
from ..core.guide_draw import guide_ticks, guide_to_drawables, segment_key
from ..core.labels import feature_hint
from ..core.registry import dispatch
from ..core.relationship import GuideLine, GuideSegment, Relationship
from ..core.resolver import resolve_rotation, resolve_scale, resolve_translation
from ..core.snap_apply import (
    BREAK,
    HOLD,
    max_active_screen_dist,
    snap_apply_mode,
)
from ..core.solvers.base import SolveContext
from ..core.spatial import broad_phase
from ..core.style import engaged_color
from ..core.tolerance import SnapHysteresis
from ..core.transform import TransformMode
from ..core.transform_snap import rotated_matrix
from ..core.view_filter import restrict_snap_axes
from ..draw import handler as draw
from ..draw.handler import GuideDrawItem
from ..preferences import get_prefs
from ..properties import (
    active_frame,
    custom_frame_object,
    enabled_families,
    enabled_snap_axes,
    get_options,
)


def world_per_pixel(region, rv3d, depth_co: Vector) -> float:
    """Return the world length of one screen pixel at ``depth_co``."""
    a = view3d_utils.region_2d_to_location_3d(region, rv3d, (0.0, 0.0), depth_co)
    b = view3d_utils.region_2d_to_location_3d(region, rv3d, (1.0, 0.0), depth_co)
    return (a - b).length or 1e-6


def feature_kind(feature: Feature) -> str:
    """Stable string kind for ranking keys."""
    kind = getattr(feature, "kind", None)
    if kind is not None and hasattr(kind, "value"):
        return kind.value
    return getattr(feature, "kind", type(feature).__name__)


def rank_key(rel: Relationship):
    """NMS identity key for a relationship."""
    return (
        rel.family,
        rel.axis,
        rel.target_entity,
        feature_kind(rel.moving),
        feature_kind(rel.target),
    )


@dataclass
class InferenceResult:
    """Output of one inference tick."""
    ranked: list[scoring.RankItem]
    active_item: scoring.RankItem | None
    snapped: bool
    active_set: list[Relationship]
    translation: Vector
    rotation_axis: Vector
    rotation_angle: float
    scale: Vector
    max_active_screen_dist: float = 0.0
    snap_apply: str = HOLD


def screen_metrics(region, rv3d, rel: Relationship):
    """Return ``(screen_dist_px, screen_anchor)`` for ``rel``."""
    moving_co = rel.moving_co
    snapped = moving_co + rel.delta.translation
    a = view3d_utils.location_3d_to_region_2d(region, rv3d, moving_co)
    b = view3d_utils.location_3d_to_region_2d(region, rv3d, snapped)
    if a is None or b is None:
        return None, None
    anchor_co = feature_anchor(rel.target)
    mid = view3d_utils.location_3d_to_region_2d(
        region, rv3d, (anchor_co + snapped) * 0.5
    )
    anchor = (mid.x, mid.y) if mid is not None else (a.x, a.y)
    return (a - b).length, anchor


def run_inference(
    context,
    *,
    region,
    rv3d,
    snapshot,
    moving: FeaturePool,
    anchor_world: Vector,
    snap: SnapHysteresis,
    transform_mode: TransformMode = TransformMode.TRANSLATE,
    frozen_world_tol: float | None = None,
) -> InferenceResult:
    """Run extract, solve, rank and resolve for one modal event.

    ``frozen_world_tol`` overrides the pixel-derived world tolerance.
    """
    options = get_options(context)
    if not options.enabled:
        return InferenceResult(
            ranked=[],
            active_item=None,
            snapped=False,
            active_set=[],
            translation=Vector((0.0, 0.0, 0.0)),
            rotation_axis=Vector((0.0, 0.0, 1.0)),
            rotation_angle=0.0,
            scale=Vector((1.0, 1.0, 1.0)),
        )

    # Pixel options are authored at 1x UI scale; match Blender's own HiDPI
    # scaling so tolerances feel the same on every display.
    px = ui_scale(context)
    passive_px = options.passive_range_px * px
    snap_px = options.snap_tolerance_px * px
    hysteresis_px = options.snap_release_hysteresis_px * px
    reengage_px = options.snap_reengage_margin_px * px

    wpp = world_per_pixel(region, rv3d, anchor_world)
    passive_world = (
        frozen_world_tol if frozen_world_tol is not None else passive_px * wpp
    )
    frame = active_frame(options)
    unit_scale, _suffix = scene_unit_info(context)
    axes = frame_axes(
        context,
        context.active_object,
        frame,
        custom_object=custom_frame_object(context, options),
    )

    nearby_feats = broad_phase(snapshot.index, anchor_world, passive_world)
    candidate_pool = FeaturePool.from_features(list(nearby_feats))

    if options.enable_tangency and snapshot.surface_index is not None:
        surfaces = surface_features_for_point(
            snapshot.surface_index,
            anchor_world,
            passive_world,
            limit=8,
        )
        append_surfaces(candidate_pool, surfaces)

    ctx = SolveContext(
        axes=axes,
        world_tol=passive_world,
        frame=frame,
        passive_px=passive_px,
        snap_px=snap_px,
        unit_scale=unit_scale,
        surface_query_limit=8,
        transform_mode=transform_mode,
        spacing_metric=options.spacing_metric,
        length_format=length_formatter(context),
    )
    rels = dispatch(moving, candidate_pool, ctx, enabled_families(options))
    rels = filter_for_view(rels, rv3d)
    rels = restrict_snap_axes(rels, enabled_snap_axes(options))

    items: list[scoring.RankItem] = []
    for rel in rels:
        sd, anchor = screen_metrics(region, rv3d, rel)
        if sd is None:
            continue
        items.append(
            scoring.RankItem(
                key=rank_key(rel),
                score=scoring.relationship_score(rel, sd, passive_px, passive_world),
                screen_dist=sd,
                payload=rel,
                screen_anchor=anchor,
            )
        )
    ranked, visible = scoring.rank(
        items,
        passive_px,
        top_k=options.max_guides,
        nms_px=options.nms_distance_px * px,
    )

    release_px = snap_px + hysteresis_px

    active_item, snapped = snap.pick_active(
        ranked,
        snap_px,
        hysteresis_px,
        visible=visible,
        reengage_margin_px=reengage_px,
    )

    active_set: list[Relationship] = []
    active_keys: set[tuple] = set()
    max_dist = 0.0
    apply_mode = HOLD

    if snapped and active_item is not None:
        active_set = build_active_set(
            active_item,
            ranked,
            snap_px=snap_px,
            release_px=release_px,
            max_constraints=options.max_guides,
            visible=visible,
            sticky_keys=snap.sticky_keys,
        )
        active_keys = {rank_key(r) for r in active_set}
        snap.remember_active_keys(active_keys)
        max_dist = max_active_screen_dist(active_keys, visible + ranked)
        apply_mode = snap_apply_mode(max_dist, snap_px, release_px)
        if apply_mode == BREAK:
            snap.force_break()
            snapped = False
            active_item = None
            active_set = []
            active_keys = set()
            max_dist = 0.0
            apply_mode = HOLD

    if snapped and active_keys:
        # Engaged guides are always drawn, even when latched from outside the
        # decluttered top-K.
        ranked = scoring.with_engaged(
            ranked, ranked + visible + [active_item], active_keys, options.max_guides
        )

    rot_axis, rot_angle = resolve_rotation(
        active_set, angle_snap_deg=options.angle_snap_increment
    )
    return InferenceResult(
        ranked=ranked,
        active_item=active_item,
        snapped=snapped,
        active_set=active_set,
        translation=resolve_translation(active_set, frame),
        rotation_axis=rot_axis,
        rotation_angle=rot_angle,
        scale=resolve_scale(active_set),
        max_active_screen_dist=max_dist,
        snap_apply=apply_mode,
    )


# ── Screen-relative sizing ─────────────────────────────────
# Guide geometry is sized from the viewport zoom at the selection's depth so it
# looks the same for millimetre jewellery and city-scale architecture.
_SPAN_VIEWPORTS = 3.0     # spanning lines reach this many viewport diagonals
_DASH_PX = 8.0            # dash / gap length on screen (at the anchor depth)
_GAP_PX = 5.0
_INTERSECT_PX = 3.0       # engaged guides this close on screen "cross"


def _span_guide_line(
    guide: GuideLine, extent: float
) -> tuple[Vector, Vector]:
    """Return a world-space segment ``extent`` long each way along the guide."""
    d = guide.direction.normalized()
    anchor = guide.point.copy()
    return (anchor - d * extent, anchor + d * extent)


def _fade_alpha(
    color: tuple,
    screen_dist: float,
    passive_px: float,
    is_active: bool,
    fade_enabled: bool,
) -> tuple:
    """Return ``color`` with proximity-faded alpha.

    Active guides are opaque; passive ones ramp from ~20 % at the passive zone
    edge to 100 % at snap distance.
    """
    r, g, b, a = color
    if is_active or not fade_enabled:
        return (r, g, b, a)
    t = max(0.0, min(1.0, screen_dist / max(passive_px, 1.0)))
    fade = 0.20 + 0.80 * (1.0 - t)
    return (r, g, b, a * fade)


def _segment_intersection_3d(
    a0: Vector, a1: Vector, b0: Vector, b1: Vector, tol: float
) -> Vector | None:
    """Return the midpoint of the closest approach of two 3D segments, or None.

    None when the segments stay farther than ``tol`` apart.
    """
    da = a1 - a0
    db = b1 - b0
    dc = b0 - a0
    dab = da.cross(db)
    denom = dab.length_squared
    if denom < 1e-12:
        return None  # parallel
    t = dc.cross(db).dot(dab) / denom
    s = dc.cross(da).dot(dab) / denom
    pa = a0 + da * t
    pb = b0 + db * s
    if (pa - pb).length > tol:
        return None
    return (pa + pb) * 0.5


def _axis_colors(context) -> dict[str, tuple] | None:
    """Theme X/Y/Z axis colours (RGBA), or None if the theme is unreadable."""
    try:
        ui = context.preferences.themes[0].user_interface
        return {
            "X": (*ui.axis_x, 1.0),
            "Y": (*ui.axis_y, 1.0),
            "Z": (*ui.axis_z, 1.0),
        }
    except (AttributeError, IndexError):
        return None


def push_guides(
    context,
    *,
    region,
    rv3d,
    result: InferenceResult,
    depth_co: Vector,
    ghost_co: Vector | None = None,
    ghost_edges: list[tuple[Vector, Vector]] | None = None,
    preview_labels: list[tuple[Vector, str]] | None = None,
):
    """Push ranked guides and the landing preview into the draw handler.

    ``depth_co`` sizes screen-relative geometry; ``ghost_co`` and ``ghost_edges``
    show the snapped landing; ``preview_labels`` are ``(world_pos, text)`` notes.
    """
    options = get_options(context)
    prefs = get_prefs(context)
    ranked = result.ranked
    snapped = result.snapped
    ghost_edges = ghost_edges or []
    preview_labels = preview_labels or []

    active_keys = {rank_key(r) for r in result.active_set} if snapped else set()
    if not options.show_passive_guides:
        # "Show guides before they engage" off: draw engaged guides only.
        ranked = [it for it in ranked if it.key in active_keys]
    if not ranked and not ghost_edges and not preview_labels:
        draw.clear_state()
        return

    active_color = tuple(prefs.guide_color_active)
    passive_color = tuple(prefs.guide_color_passive)
    use_axis_colors = getattr(prefs, "guide_color_mode", "AXIS") == "AXIS"
    axis_colors = _axis_colors(context) if use_axis_colors else None
    px = ui_scale(context)
    passive_px = options.passive_range_px * px
    extend_vp = getattr(options, "extend_guides_to_viewport", True)
    fade_enabled = prefs.guide_fade_passive

    wpp = world_per_pixel(region, rv3d, depth_co)
    diag_px = (region.width**2 + region.height**2) ** 0.5
    span_extent = wpp * diag_px * _SPAN_VIEWPORTS

    guide_items: list[GuideDrawItem] = []
    tick_items: list[GuideDrawItem] = []
    snap_dots: list[tuple[Vector, tuple]] = []
    intersection_dots: list[Vector] = []
    labels = []
    tick_size = wpp * 8.0 * px

    # Engaged guide *lines* only: span bars, caps and circles are glyphs, and
    # crossing them would scatter meaningless intersection dots.
    active_segments: list[tuple[Vector, Vector]] = []
    # Segment identity -> index in guide_items, so a segment two guides share
    # is drawn once (translucent overdraw reads brighter), engaged copy kept.
    drawn: dict[tuple, int] = {}
    dedupe_eps = max(wpp * 0.25, 1e-9)

    for item in ranked:
        rel = item.payload
        is_active = snapped and item.key in active_keys
        moving_co = rel.moving_co + (
            rel.delta.translation if is_active else Vector((0, 0, 0))
        )

        if is_active:
            base_color = engaged_color(
                rel.family,
                rel.axis,
                use_axis_colors=use_axis_colors,
                active_color=active_color,
                axis_colors=axis_colors,
            )
        else:
            base_color = passive_color
        color = _fade_alpha(base_color, item.screen_dist, passive_px, is_active, fade_enabled)

        if extend_vp and isinstance(rel.guide, GuideLine):
            segs = [_span_guide_line(rel.guide, span_extent)]
        else:
            segs = guide_to_drawables(rel.guide, moving_co)

        is_line = isinstance(rel.guide, (GuideLine, GuideSegment))
        for seg in segs:
            draw_item = GuideDrawItem(a=seg[0], b=seg[1], color=color, active=is_active)
            key = segment_key(seg[0], seg[1], dedupe_eps)
            index = drawn.get(key)
            if index is None:
                drawn[key] = len(guide_items)
                guide_items.append(draw_item)
            elif is_active and not guide_items[index].active:
                guide_items[index] = draw_item
            if is_active and is_line:
                active_segments.append(seg)

        # Ticks mark the two reference points, not the spanning line's ends.
        if options.show_guide_ticks and isinstance(rel.guide, GuideLine):
            tick_color = (color[0], color[1], color[2], color[3] * 0.85)
            for ta, tb in guide_ticks(
                rel.guide.point, moving_co, rel.guide.direction, tick_size
            ):
                tick_items.append(GuideDrawItem(a=ta, b=tb, color=tick_color))

        if is_active and prefs.show_snap_dot:
            snap_dots.append((feature_anchor(rel.target), color))

        # Label only engaged guides: approaching guides stay quiet so the
        # viewport is not buried in text while dragging.
        if is_active:
            hint = feature_hint(rel.target) if options.show_feature_hints else ""
            anchor_co = feature_anchor(rel.target)
            labels.append(((anchor_co + moving_co) * 0.5, rel.label, hint, color))

    if prefs.show_intersection_dot and len(active_segments) >= 2:
        tol = wpp * _INTERSECT_PX * px
        for i, (a0, a1) in enumerate(active_segments):
            for j, (b0, b1) in enumerate(active_segments):
                if j <= i:
                    continue
                pt = _segment_intersection_3d(a0, a1, b0, b1, tol)
                if pt is not None:
                    intersection_dots.append(pt)

    for world_pos, text in preview_labels:
        labels.append((world_pos, text, "", active_color))

    ghost_points = [ghost_co] if ghost_co is not None else []

    draw.set_state(
        guide_items,
        tick_items,
        snap_dots,
        intersection_dots,
        labels,
        active=snapped,
        active_color=active_color,
        passive_color=passive_color,
        line_width=prefs.guide_line_width,
        solid_lines=prefs.guide_solid_lines,
        show_snap_dot=prefs.show_snap_dot,
        snap_dot_radius_px=prefs.snap_dot_radius_px,
        show_intersection_dot=prefs.show_intersection_dot,
        pulse_enabled=prefs.guide_active_pulse,
        ghost_points=ghost_points,
        ghost_edges=ghost_edges,
        dash_world=wpp * _DASH_PX * px,
        gap_world=wpp * _GAP_PX * px,
    )


def set_world_location(obj, world_co: Vector):
    """Set ``obj``'s world translation to ``world_co``."""
    mw = obj.matrix_world.copy()
    mw.translation = world_co
    obj.matrix_world = mw


def apply_object_rotation(obj, axis: Vector, angle: float, pivot: Vector):
    """Rotate ``obj`` by ``angle`` (radians) about ``axis`` through ``pivot``."""
    if abs(angle) < 1e-9:
        return
    obj.matrix_world = rotated_matrix(obj.matrix_world, axis, angle, pivot)


def apply_object_scale(obj, scale: Vector, pivot: Vector):
    """Scale ``obj`` per axis by ``scale`` about ``pivot``."""
    if abs(scale.x - 1.0) < 1e-9 and abs(scale.y - 1.0) < 1e-9 and abs(scale.z - 1.0) < 1e-9:
        return
    mw = obj.matrix_world.copy()
    offset = mw.translation - pivot
    mw.translation = pivot + Vector(
        offset[i] * scale[i] for i in range(3)
    )
    obj.matrix_world = mw
    obj.scale = Vector(obj.scale[i] * scale[i] for i in range(3))
