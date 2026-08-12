"""Shared modal inference pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from bpy_extras import view3d_utils
from mathutils import Vector

from ..adapters.frames import frame_axes
from ..adapters.surface import append_surfaces, surface_features_for_point
from ..adapters.units import scene_unit_info
from ..adapters.view import filter_for_view
from ..core import scoring
from ..core import solvers as _solvers  # noqa: F401 - register solver table
from ..core.features import Feature, FeaturePool, feature_anchor
from ..core.graph import build_active_set
from ..core.guide_draw import guide_to_drawables
from ..core.labels import feature_hint
from ..core.registry import dispatch
from ..core.relationship import GuideLine, Relationship
from ..core.resolver import resolve_rotation, resolve_scale, resolve_translation
from ..core.snap_apply import (
    BREAK,
    HOLD,
    max_active_screen_dist,
    snap_apply_mode,
)
from ..core.solvers.base import SolveContext
from ..core.spatial import broad_phase
from ..core.tolerance import SnapHysteresis
from ..core.transform import TransformMode
from ..core.transform_snap import rotated_matrix
from ..core.view_filter import restrict_snap_axes
from ..draw import handler as draw
from ..draw.glyphs import guide_ticks
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
    """World units per screen pixel at ``depth_co``.

    Args:
        region: 3D region.
        rv3d: Region view 3D.
        depth_co: World depth reference.

    Returns:
        World length of one pixel.
    """
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
    """Screen distance and anchor for a relationship.

    Args:
        region: 3D region.
        rv3d: Region view 3D.
        rel: Relationship.
        cursor: Optional cursor region coordinates.

    Returns:
        ``(screen_dist_px, screen_anchor)``.
    """
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
    """Run extract → solve → rank → resolve for one modal event.

    Args:
        context: Blender context.
        region: Active 3D region.
        rv3d: Region view 3D.
        snapshot: Cached scene features for the interaction.
        moving: Features for the transformed selection.
        anchor_world: World-space anchor used for screen projection.
        snap: Engage/hold/break hysteresis state.
        transform_mode: Translate, rotate, or scale.
        frozen_world_tol: Optional fixed world tolerance overriding pixel scale.

    Returns:
        Ranked guides and the resolved transform deltas.
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

    wpp = world_per_pixel(region, rv3d, anchor_world)
    passive_world = (
        frozen_world_tol
        if frozen_world_tol is not None
        else options.passive_range_px * wpp
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
        passive_px=options.passive_range_px,
        snap_px=options.snap_tolerance_px,
        unit_scale=unit_scale,
        surface_query_limit=8,
        transform_mode=transform_mode,
        spacing_metric=options.spacing_metric,
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
                score=scoring.relationship_score(
                    rel, sd, options.passive_range_px, passive_world
                ),
                screen_dist=sd,
                payload=rel,
                screen_anchor=anchor,
            )
        )
    ranked, visible = scoring.rank(
        items,
        options.passive_range_px,
        top_k=options.max_guides,
        nms_px=options.nms_distance_px,
    )

    snap_px = options.snap_tolerance_px
    release_px = snap_px + options.snap_release_hysteresis_px
    reengage_px = getattr(options, "snap_reengage_margin_px", 12)

    active_item, snapped = snap.pick_active(
        ranked,
        snap_px,
        options.snap_release_hysteresis_px,
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


# ── Viewport spanning ─────────────────────────────────────
# For GuideLine types we extend segments to a large world distance so they
# appear to cross the entire viewport regardless of scene scale.  800 BU is
# enough for anything from millimetre jewellery to city-scale architecture.
_SPAN_EXTENT = 800.0


def _span_guide_line(guide: GuideLine, moving_co: Vector) -> tuple[Vector, Vector]:
    """Return a very long world-space segment along the guide axis."""
    d = guide.direction.normalized()
    anchor = guide.point.copy()
    return (anchor - d * _SPAN_EXTENT, anchor + d * _SPAN_EXTENT)


def _fade_alpha(
    color: tuple,
    screen_dist: float,
    passive_px: float,
    is_active: bool,
    fade_enabled: bool,
) -> tuple:
    """Return colour with proximity-faded alpha.

    Active guides are always full alpha.  Passive guides ramp from ~20 % at
    the edge of the passive zone to 100 % at snap distance.
    """
    r, g, b, a = color
    if is_active or not fade_enabled:
        return (r, g, b, a)
    # Normalised distance: 0 = right on target, 1 = at passive zone edge
    t = max(0.0, min(1.0, screen_dist / max(passive_px, 1.0)))
    # Fade: starts at 20 % and grows to 100 % as t → 0
    fade = 0.20 + 0.80 * (1.0 - t)
    return (r, g, b, a * fade)


def _segment_intersection_3d(
    a0: Vector, a1: Vector, b0: Vector, b1: Vector
) -> Vector | None:
    """Closest point between two line segments in 3D (for intersection dots).

    Returns the midpoint of the closest approach if within a small threshold,
    otherwise None.
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
    if (pa - pb).length > 0.05:
        return None
    return (pa + pb) * 0.5


def push_guides(
    context,
    *,
    region,
    rv3d,
    result: InferenceResult,
    depth_co: Vector,
    ghost_co: Vector | None = None,
):
    """Push ranked guides into the draw handler.

    Args:
        ranked: Ranked guide items.
        active_item: Currently engaged item, if any.
        prefs: Add-on preferences for colors.
        options: Scene options.
        unit_scale: Scene unit scale.
        region: 3D region.
        rv3d: Region view 3D.
    """
    options = get_options(context)
    prefs = get_prefs(context)
    ranked = result.ranked
    snapped = result.snapped

    if not ranked or (not snapped and not options.show_passive_guides):
        draw.clear_state()
        return

    active_keys = {rank_key(r) for r in result.active_set} if snapped else set()
    active_color = tuple(prefs.guide_color_active)
    passive_color = tuple(prefs.guide_color_passive)
    passive_px = options.passive_range_px
    extend_vp = getattr(options, "extend_guides_to_viewport", True)
    fade_enabled = getattr(options, "guide_fade_passive", True) and prefs.guide_fade_passive

    guide_items: list[GuideDrawItem] = []
    tick_items: list[GuideDrawItem] = []
    snap_dots: list[Vector] = []
    intersection_dots: list[Vector] = []
    labels = []
    tick_size = world_per_pixel(region, rv3d, depth_co) * 8.0

    # Collect guide segments keyed for intersection detection
    active_segments: list[tuple[Vector, Vector]] = []

    for item in ranked:
        rel = item.payload
        is_active = snapped and item.key in active_keys
        apply_delta = is_active
        moving_co = rel.moving_co + (
            rel.delta.translation if apply_delta else Vector((0, 0, 0))
        )

        base_color = active_color if is_active else passive_color
        color = _fade_alpha(base_color, item.screen_dist, passive_px, is_active, fade_enabled)

        # Build world-space segments
        if extend_vp and isinstance(rel.guide, GuideLine):
            segs = [_span_guide_line(rel.guide, moving_co)]
        else:
            segs = guide_to_drawables(rel.guide, moving_co)

        for seg in segs:
            guide_items.append(GuideDrawItem(a=seg[0], b=seg[1], color=color))
            if is_active:
                active_segments.append(seg)

        # Ticks at the two reference points (not on spanning lines)
        if options.show_guide_ticks and isinstance(rel.guide, GuideLine):
            tick_color = (color[0], color[1], color[2], color[3] * 0.85)
            for ta, tb in guide_ticks(
                rel.guide.point, moving_co, rel.guide.direction, tick_size
            ):
                tick_items.append(GuideDrawItem(a=ta, b=tb, color=tick_color))

        # Snap dot: place at the target feature anchor
        if is_active and prefs.show_snap_dot:
            anchor_co = feature_anchor(rel.target)
            snap_dots.append(anchor_co)

        hint = feature_hint(rel.target) if options.show_feature_hints else ""
        anchor_co = feature_anchor(rel.target)
        labels.append(((anchor_co + moving_co) * 0.5, rel.label, hint))

    # Intersection dots between all pairs of active segments
    if prefs.show_intersection_dot and len(active_segments) >= 2:
        for i, (a0, a1) in enumerate(active_segments):
            for j, (b0, b1) in enumerate(active_segments):
                if j <= i:
                    continue
                pt = _segment_intersection_3d(a0, a1, b0, b1)
                if pt is not None:
                    intersection_dots.append(pt)

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
    )


def set_world_location(obj, world_co: Vector):
    """Set an object's world translation.

    Args:
        obj: Blender object.
        location: World-space location.
    """
    mw = obj.matrix_world.copy()
    mw.translation = world_co
    obj.matrix_world = mw


def apply_object_rotation(obj, axis: Vector, angle: float, pivot: Vector):
    """Apply a rotation delta about ``pivot``.

    Args:
        obj: Blender object.
        axis: Rotation axis.
        angle: Angle in radians.
        pivot: World-space pivot.
    """
    if abs(angle) < 1e-9:
        return
    # Delegate to the unit-tested core helper so the rotate math lives in one
    # place. Setting the translation before ``rot @ mw`` (as this used to) would
    # re-rotate the origin twice, orbiting an off-world-origin object about the
    # pivot instead of spinning it in place.
    obj.matrix_world = rotated_matrix(obj.matrix_world, axis, angle, pivot)


def apply_object_scale(obj, scale: Vector, pivot: Vector):
    """Apply a scale delta about ``pivot``.

    Args:
        obj: Blender object.
        scale: Per-axis scale factors.
        pivot: World-space pivot.
    """
    if abs(scale.x - 1.0) < 1e-9 and abs(scale.y - 1.0) < 1e-9 and abs(scale.z - 1.0) < 1e-9:
        return
    mw = obj.matrix_world.copy()
    offset = mw.translation - pivot
    mw.translation = pivot + Vector(
        offset[i] * scale[i] for i in range(3)
    )
    obj.matrix_world = mw
    obj.scale = Vector(obj.scale[i] * scale[i] for i in range(3))
