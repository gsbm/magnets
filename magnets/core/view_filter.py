"""View-plane visibility filtering for guides (no bpy)."""

from __future__ import annotations

import math

from mathutils import Vector

from .relationship import (
    GuideCircle,
    GuideLine,
    GuidePlane,
    GuideSegment,
    GuideSpans,
    Relationship,
)


def guide_direction_visible(
    direction: Vector,
    view_normal: Vector,
    *,
    parallel_threshold: float = 0.15,
) -> bool:
    """Return False when a guide runs into or out of the screen.

    Visible guides lie in the view plane, perpendicular to the view normal.
    """
    if view_normal.length_squared < 1e-12 or direction.length_squared < 1e-12:
        return True
    n = view_normal.normalized()
    d = direction.normalized()
    return abs(d.dot(n)) < (1.0 - parallel_threshold)


def relationship_visible_in_view(
    rel: Relationship,
    view_normal: Vector | None,
    *,
    parallel_threshold: float = 0.15,
) -> bool:
    """Return False if ``rel`` should be hidden and non-magnetic in this view.

    A relationship is hidden when its snap axis points into the screen (it can
    be neither seen nor applied: the release commit drops the depth axis), or
    when its guide would be seen end-on.
    """
    if view_normal is None:
        return True

    constraint_dir = getattr(rel, "constraint_dir", None)
    if constraint_dir is not None and not guide_direction_visible(
        constraint_dir, view_normal, parallel_threshold=parallel_threshold
    ):
        return False

    guide = rel.guide
    if isinstance(guide, GuideLine):
        return guide_direction_visible(
            guide.direction, view_normal, parallel_threshold=parallel_threshold
        )
    if isinstance(guide, GuideSegment):
        seg = guide.b - guide.a
        return guide_direction_visible(
            seg, view_normal, parallel_threshold=parallel_threshold
        )
    if isinstance(guide, GuideSpans):
        # Hide when the spacing axis is nearly parallel to the view normal.
        return guide_direction_visible(
            guide.axis, view_normal, parallel_threshold=parallel_threshold
        )
    if isinstance(guide, GuideCircle):
        # Hidden edge-on (normal in the view plane), where it reads as a line.
        # Facing the viewer it is fully visible and snaps within the view.
        return not _edge_on(guide.normal, view_normal, parallel_threshold)
    if isinstance(guide, GuidePlane):
        # Seen edge-on a plane reads as a line and snaps within the view;
        # facing the viewer it fills the view and snaps along the depth axis.
        return guide_direction_visible(
            guide.normal, view_normal, parallel_threshold=parallel_threshold
        )
    return True


def _edge_on(normal: Vector, view_normal: Vector, threshold: float) -> bool:
    if normal.length_squared < 1e-12 or view_normal.length_squared < 1e-12:
        return False
    return abs(normal.normalized().dot(view_normal.normalized())) < threshold


def filter_relationships_for_view(
    rels: list[Relationship],
    view_normal: Vector | None,
    *,
    parallel_threshold: float = 0.15,
) -> list[Relationship]:
    """Drop relationships invisible in the view (``view_normal`` None keeps all)."""
    if view_normal is None:
        return rels
    return [
        rel
        for rel in rels
        if relationship_visible_in_view(rel, view_normal, parallel_threshold=parallel_threshold)
    ]


def depth_threshold(cutoff_rad: float) -> float:
    """``parallel_threshold`` hiding directions within ``cutoff_rad`` of the view."""
    return 1.0 - math.cos(max(0.0, cutoff_rad))


def restrict_snap_axes(
    rels: list[Relationship],
    enabled_axes: set[str],
) -> list[Relationship]:
    """Drop alignment relationships whose axis is not in ``enabled_axes``."""
    return [
        rel
        for rel in rels
        if rel.family != "alignment" or rel.axis in enabled_axes
    ]
