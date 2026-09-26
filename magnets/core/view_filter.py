"""View-plane visibility filtering for guides (no bpy)."""

from __future__ import annotations

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
    """Return False if ``rel`` should be hidden and non-magnetic in this view."""
    if view_normal is None:
        return True

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
        return guide_direction_visible(
            guide.normal, view_normal, parallel_threshold=parallel_threshold
        )
    if isinstance(guide, GuidePlane):
        n = guide.normal.normalized()
        vn = view_normal.normalized()
        # Plane shown edge-on when its normal lies in the view plane.
        return abs(n.dot(vn)) > (1.0 - parallel_threshold)
    return True


def filter_relationships_for_view(
    rels: list[Relationship],
    view_normal: Vector | None,
) -> list[Relationship]:
    """Drop relationships invisible in the view (``view_normal`` None keeps all)."""
    if view_normal is None:
        return rels
    return [rel for rel in rels if relationship_visible_in_view(rel, view_normal)]


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
