"""Shared modal inference pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
from bpy_extras import view3d_utils
from mathutils import Vector

from ..adapters.frames import frame_axes
from ..adapters.surface import append_surfaces, surface_features_for_point
from ..adapters.units import length_formatter, scene_unit_info
from ..adapters.view import ui_scale, view_normal_world
from ..core import scoring
from ..core import solvers as _solvers  # noqa: F401 - register solver table
from ..core.families import families_for_mode
from ..core.features import Feature, FeaturePool, feature_anchor
from ..core.frames import world_axes
from ..core.graph import build_active_set, coincident_targets, one_guide_per_direction
from ..core.guide_draw import (
    axis_route,
    endpoint_ticks,
    guide_ticks,
    guide_to_drawables,
    segment_key,
)
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
from ..core.view_filter import (
    depth_threshold,
    filter_relationships_for_view,
    restrict_snap_axes,
    restrict_to_axis_mask,
)
from ..core.view_lod import FAR_FAMILIES, ViewLOD, far_moving
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

# "Prioritize Nearby Objects" (``core.view_lod``): objects off screen are
# ignored; the ones nearest the selection on screen, plus its row/column
# neighbours, get every guide; the rest only alignment near snapping.
NEARBY_MAX = 8
NEARBY_ROW_NEIGHBOURS = 2


def world_per_pixel(region, rv3d, depth_co: Vector) -> float:
    """Return the world length of one screen pixel at ``depth_co``."""
    a = view3d_utils.region_2d_to_location_3d(region, rv3d, (0.0, 0.0), depth_co)
    b = view3d_utils.region_2d_to_location_3d(region, rv3d, (1.0, 0.0), depth_co)
    return (a - b).length or 1e-6


def _view_ray(rv3d, point: Vector) -> Vector | None:
    """World direction from the viewer to ``point`` (perspective views)."""
    try:
        eye = rv3d.view_matrix.inverted().translation
    except ValueError:  # singular view matrix
        return None
    ray = point - eye
    if ray.length_squared < 1e-12:
        return None
    return ray.normalized()


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
    # Engaged alignment rank key -> other objects' targets on the same
    # coordinate (drawn as marks on the one guide line).
    coincident: dict | None = None
    # Alignment frame axes (name -> unit vector), for routing guides.
    axes: dict | None = None


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


def _screen_dist_fn(region, rv3d):
    """``(moving_co, correction) -> px`` with the same math as ``_rank_items``."""
    project = view3d_utils.location_3d_to_region_2d
    cache: dict[tuple, object] = {}

    def screen_dist(moving_co: Vector, correction: Vector) -> float | None:
        key = moving_co.to_tuple()
        if key in cache:
            a = cache[key]
        else:
            a = cache[key] = project(region, rv3d, moving_co)
        if a is None:
            return None
        b = project(region, rv3d, moving_co + correction)
        if b is None:
            return None
        return (a - b).length

    return screen_dist


def _rank_items(
    rels: list[Relationship],
    region,
    rv3d,
    passive_px: float,
    passive_world: float,
) -> list[scoring.RankItem]:
    """Score ``rels`` into RankItems, keeping those within ``passive_px``.

    Same keys, scores and distances as ``rank_key`` + ``relationship_score``
    + ``screen_metrics`` per relationship, but only in-range items are ever
    ranked, held or drawn (``scoring.rank`` drops the rest), so the distance
    is measured first and keys and scores are built for those alone. Each
    moving feature is projected once, not once per relationship. The screen
    anchor is left unset: ranking suppresses one guide per slot and never
    reads it.
    """
    project = view3d_utils.location_3d_to_region_2d
    moving_2d: dict[int, object] = {}
    kinds: dict[int, str] = {}

    def kind_of(feature) -> str:
        fid = id(feature)
        kind = kinds.get(fid)
        if kind is None:
            kind = kinds[fid] = feature_kind(feature)
        return kind

    items: list[scoring.RankItem] = []
    # Items equal in (key, score, distance) sort next to each other and every
    # consumer takes the first of them, so later ones never matter.
    seen: set[tuple] = set()
    # A scale snap does not move anything on screen: its distance is the size
    # difference in pixels, so it engages within the snap zone like the rest.
    px_per_world = passive_px / max(passive_world, 1e-12)
    for rel in rels:
        if abs(rel.delta.scale_factor - 1.0) > 1e-9:
            sd = rel.residual * px_per_world
        else:
            moving = rel.moving
            moving_co = feature_anchor(moving)
            mid = id(moving)
            if mid in moving_2d:
                a = moving_2d[mid]
            else:
                a = moving_2d[mid] = project(region, rv3d, moving_co)
            if a is None:
                continue
            snapped = moving_co + rel.delta.translation
            b = project(region, rv3d, snapped)
            if b is None:
                continue
            sd = (a - b).length
        if sd > passive_px:
            continue
        target = rel.targets[0]
        key = (rel.family, rel.axis, target.entity, kind_of(rel.moving), kind_of(target))
        score = scoring.relationship_score(rel, sd, passive_px, passive_world)
        if (key, score, sd) in seen:
            continue
        seen.add((key, score, sd))
        items.append(
            scoring.RankItem(key=key, score=score, screen_dist=sd, payload=rel)
        )
    # Per rank key only the best item is ever shown, engaged or measured.
    return scoring.best_per_key(items)


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
    axis_mask: tuple | None = None,
) -> InferenceResult:
    """Run extract, solve, rank and resolve for one modal event.

    ``frozen_world_tol`` overrides the pixel-derived world tolerance.
    ``axis_mask`` (three booleans, global X/Y/Z) is a native axis lock: guides
    that could not move the selection under it are dropped.
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
    if transform_mode == TransformMode.SCALE:
        # The scale release snaps only within the snap tolerance (it matches
        # sizes directly, without the latch), so an equal-size guide shown as
        # engaged must not be held any further than that.
        hysteresis_px = 0.0
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

    projection = (
        tuple(tuple(row) for row in rv3d.perspective_matrix),
        region.width,
        region.height,
    )
    families = families_for_mode(transform_mode, enabled_families(options))
    # Depth Axis Cutoff: the depth direction is the view direction (ortho) or
    # the view ray through the selection (perspective).
    depth_dir = view_normal_world(rv3d) or _view_ray(rv3d, anchor_world)
    depth_thr = depth_threshold(getattr(options, "depth_axis_cutoff", math.radians(30.0)))
    far_pool = None
    if getattr(options, "prioritize_nearby", True):
        lod = getattr(snapshot, "view_lod", None)
        if lod is None:
            lod = snapshot.view_lod = ViewLOD(snapshot.pool)
        tiers = lod.tiers(
            projection,
            np.array([tuple(p.co) for p in moving.points], dtype=np.float64),
            margin_px=passive_px,
            max_near=NEARBY_MAX,
            row_neighbours=NEARBY_ROW_NEIGHBOURS,
        )
        # The screen tiers replace the broad phase (whose radius spans the
        # scene anyway).
        candidate_pool, far_pool = lod.pools(tiers, families)
    else:
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
        view_normal=depth_dir,
        depth_threshold=depth_thr,
        screen_dist=_screen_dist_fn(region, rv3d),
        projection=projection,
        allow_diagonal=options.allow_diagonal_guides,
    )
    rels = dispatch(moving, candidate_pool, ctx, families)
    if far_pool is not None:
        # Far objects only feed alignment, and only near the snap zone.
        far_ctx = replace(
            ctx,
            max_screen_px=snap_px + hysteresis_px,
        )
        rels += dispatch(far_moving(moving), far_pool, far_ctx, families & FAR_FAMILIES)
    rels = filter_relationships_for_view(rels, depth_dir, parallel_threshold=depth_thr)
    rels = restrict_snap_axes(rels, enabled_snap_axes(options))
    rels = restrict_to_axis_mask(rels, axis_mask)

    items = _rank_items(rels, region, rv3d, passive_px, passive_world)
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
        tie_px=scoring.TIE_PX * px,
        switch_px=scoring.SWITCH_PX * px,
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
            tie_px=scoring.TIE_PX * px,
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

    engaged: list[scoring.RankItem] = []
    coincident: dict = {}
    if snapped and active_keys:
        # Engaged guides are always drawn, even when latched from outside the
        # decluttered top-K.
        ranked = scoring.with_engaged(
            ranked, ranked + visible + [active_item], active_keys, options.max_guides
        )
        engaged = [it for it in ranked if it.key in active_keys]
        for rel in active_set:
            marks = coincident_targets(rel, visible)
            if marks:
                coincident[rank_key(rel)] = marks
    # One guide per direction on screen: engaged first, then passive guides
    # only for directions still free.
    ranked = one_guide_per_direction(engaged, visible, options.max_guides)

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
        coincident=coincident,
        axes=axes,
    )


# ── Screen-relative sizing ─────────────────────────────────
# Guide geometry is sized from the viewport zoom at the selection's depth so it
# looks the same for millimetre jewellery and city-scale architecture.
_SPAN_VIEWPORTS = 3.0     # spanning lines reach this many viewport diagonals
_DASH_PX = 8.0            # dash / gap length on screen (at the anchor depth)
_GAP_PX = 5.0
_INTERSECT_PX = 3.0       # engaged guides this close on screen "cross"


# Routed alignment guides reach this far past their two ends (1x UI px).
_ROUTE_OVERSHOOT_PX = 10.0


def _is_routed_alignment(rel: Relationship) -> bool:
    """Alignment guides are drawn along the frame axes (``axis_route``)."""
    return (
        rel.family == "alignment"
        and rel.constraint_dir is not None
        and isinstance(rel.guide, GuideLine)
    )


def _tick(point: Vector, along: Vector, size: float, color) -> GuideDrawItem:
    """A tick across ``along`` at ``point``."""
    a, b = endpoint_ticks(point, along, size)
    return GuideDrawItem(a=a, b=b, color=color)


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
    # crossing them would scatter meaningless intersection dots. Each entry
    # remembers its guide, so an L's own legs do not mark a crossing.
    active_segments: list[tuple[tuple[Vector, Vector], int]] = []
    route_axes = list((result.axes or world_axes()).values())
    # Segment identity -> index in guide_items, so a segment two guides share
    # is drawn once (translucent overdraw reads brighter), engaged copy kept.
    drawn: dict[tuple, int] = {}
    dedupe_eps = max(wpp * 0.25, 1e-9)

    for guide_index, item in enumerate(ranked):
        rel = item.payload
        is_active = snapped and item.key in active_keys
        moving_co = rel.moving_co + (
            rel.delta.translation if is_active else Vector((0, 0, 0))
        )

        # Lines use the Active Color; the axis color goes on the label. An
        # alignment line runs across its axis (in the shared plane), so a red
        # line for an X match would read as "along X", which it is not.
        base_color = active_color if is_active else passive_color
        label_color = engaged_color(
            rel.family,
            rel.axis,
            use_axis_colors=use_axis_colors,
            active_color=active_color,
            axis_colors=axis_colors,
        )
        color = _fade_alpha(base_color, item.screen_dist, passive_px, is_active, fade_enabled)

        routed = _is_routed_alignment(rel)
        if routed:
            # Along the frame axes in the shared plane: one segment or an L.
            segs = axis_route(
                rel.guide.point,
                moving_co,
                rel.constraint_dir,
                route_axes,
                min_leg=wpp * 1.0 * px,
                overshoot=wpp * _ROUTE_OVERSHOOT_PX * px,
            )
        elif extend_vp and isinstance(rel.guide, GuideLine):
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
            # A routed guide only meets another where both reach the moving
            # object: its last leg; crossings of the other legs mean nothing.
            if is_active and is_line and (not routed or seg is segs[-1]):
                active_segments.append((seg, guide_index))

        # Ticks mark the two reference points, not the spanning line's ends.
        if options.show_guide_ticks and routed and segs:
            tick_color = (color[0], color[1], color[2], color[3] * 0.85)
            first, last = segs[0], segs[-1]
            tick_items.append(_tick(rel.guide.point, first[1] - first[0], tick_size, tick_color))
            tick_items.append(_tick(last[1], last[1] - last[0], tick_size, tick_color))
        elif options.show_guide_ticks and isinstance(rel.guide, GuideLine):
            tick_color = (color[0], color[1], color[2], color[3] * 0.85)
            for ta, tb in guide_ticks(
                rel.guide.point, moving_co, rel.guide.direction, tick_size
            ):
                tick_items.append(GuideDrawItem(a=ta, b=tb, color=tick_color))

        # Other objects on the same coordinate: a small cross in the shared
        # plane at each, instead of a line each.
        if is_active and options.show_guide_ticks and routed:
            for co in (result.coincident or {}).get(item.key, ()):
                for axis in route_axes:
                    if abs(axis.normalized().dot(rel.constraint_dir.normalized())) < 0.5:
                        ta, tb = endpoint_ticks(co, axis.cross(rel.constraint_dir), tick_size)
                        tick_items.append(GuideDrawItem(a=ta, b=tb, color=color))

        if is_active and prefs.show_snap_dot:
            snap_dots.append((feature_anchor(rel.target), color))

        # Label only engaged guides: approaching guides stay quiet so the
        # viewport is not buried in text while dragging.
        if is_active:
            hint = feature_hint(rel.target) if options.show_feature_hints else ""
            anchor_co = feature_anchor(rel.target)
            labels.append(((anchor_co + moving_co) * 0.5, rel.label, hint, label_color))

    if prefs.show_intersection_dot and len(active_segments) >= 2:
        tol = wpp * _INTERSECT_PX * px
        for i, ((a0, a1), gi) in enumerate(active_segments):
            for j, ((b0, b1), gj) in enumerate(active_segments):
                if j <= i or gi == gj:
                    continue
                pt = _segment_intersection_3d(a0, a1, b0, b1, tol)
                if pt is not None and all((pt - q).length > tol for q in intersection_dots):
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
