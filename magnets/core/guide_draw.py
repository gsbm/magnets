"""Convert Guide objects into drawable segments (no bpy)."""

from __future__ import annotations

import math

from mathutils import Vector

from .relationship import (
    Guide,
    GuideCircle,
    GuideLine,
    GuidePlane,
    GuideSegment,
    GuideSpans,
)


def _perpendicular_unit(direction: Vector) -> Vector:
    d = direction.normalized()
    helper = Vector((0.0, 0.0, 1.0))
    if abs(d.dot(helper)) > 0.95:
        helper = Vector((0.0, 1.0, 0.0))
    return d.cross(helper).normalized()


def axis_parallel_segment(
    anchor: Vector,
    direction: Vector,
    extent_point: Vector,
    margin: float = 0.25,
):
    """Return ``(p0, p1)`` along ``direction`` through ``anchor``.

    The segment reaches ``extent_point``, extended by the ``margin`` fraction.
    """
    if direction.length_squared == 0.0:
        return (anchor.copy(), anchor.copy())
    d = direction.normalized()
    t = d.dot(extent_point - anchor)
    dvec = anchor + d * t - anchor
    a = anchor - dvec * margin
    b = anchor + d * t + dvec * margin
    return (a, b)


def endpoint_ticks(
    point: Vector,
    direction: Vector,
    size: float = 0.08,
) -> tuple[Vector, Vector]:
    """Return a tick of length ``size`` across ``direction`` at ``point``."""
    n = _perpendicular_unit(direction)
    half = size * 0.5
    return (point - n * half, point + n * half)


def guide_ticks(
    anchor: Vector,
    extent: Vector,
    direction: Vector,
    size: float = 0.08,
) -> list[tuple[Vector, Vector]]:
    """Return ticks across ``direction`` at ``anchor`` and ``extent``."""
    return [endpoint_ticks(anchor, direction, size), endpoint_ticks(extent, direction, size)]


def circle_segments(
    center: Vector,
    normal: Vector,
    radius: float,
    segments: int = 32,
) -> list[tuple[Vector, Vector]]:
    """Approximate a circle as ``segments`` consecutive line segments."""
    if radius <= 0.0:
        return []
    n = _perpendicular_unit(normal)
    tangent = normal.cross(n).normalized()
    out: list[tuple[Vector, Vector]] = []
    prev = center + tangent * radius
    for i in range(1, segments + 1):
        ang = (2.0 * math.pi * i) / segments
        pt = center + tangent * (math.cos(ang) * radius) + n * (math.sin(ang) * radius)
        out.append((prev.copy(), pt.copy()))
        prev = pt
    return out


def plane_cross(
    point: Vector,
    normal: Vector,
    size: float = 0.25,
) -> list[tuple[Vector, Vector]]:
    """Return two segments forming a cross of arm ``size`` on a plane."""
    n = _perpendicular_unit(normal)
    t = normal.cross(n).normalized()
    half = size * 0.5
    return [
        (point - t * half, point + t * half),
        (point - n * half, point + n * half),
    ]


def equal_span_marks(
    start: Vector,
    end: Vector,
    axis: Vector,
) -> list[tuple[Vector, Vector]]:
    """Return bar, end-cap, and hash strokes for one equal gap along ``axis``."""
    length = (end - start).length
    if length < 1e-9:
        return [(start.copy(), end.copy())]
    perp = _perpendicular_unit(axis)
    tick = perp * (length * 0.12)
    cap = perp * (length * 0.09)
    off = axis.normalized() * (length * 0.05)
    mid = (start + end) * 0.5
    return [
        (start.copy(), end.copy()),
        (start + cap, start - cap),
        (end + cap, end - cap),
        (mid + off + tick, mid + off - tick),
        (mid - off + tick, mid - off - tick),
    ]


def segment_key(a: Vector, b: Vector, eps: float = 1e-6) -> tuple:
    """Orientation-free identity of segment ``a``-``b``, quantised to ``eps``."""
    qa = tuple(round(v / eps) for v in a)
    qb = tuple(round(v / eps) for v in b)
    return (qa, qb) if qa <= qb else (qb, qa)


def dedupe_segments(
    segments: list[tuple[Vector, Vector]],
    eps: float = 1e-6,
) -> list[tuple[Vector, Vector]]:
    """Drop segments identical to an earlier one (either direction).

    Overdrawn duplicates render brighter where guides are translucent.
    """
    seen: set[tuple] = set()
    out: list[tuple[Vector, Vector]] = []
    for a, b in segments:
        key = segment_key(a, b, eps)
        if key in seen:
            continue
        seen.add(key)
        out.append((a, b))
    return out


def guide_to_drawables(
    guide: Guide,
    moving_co: Vector,
) -> list[tuple[Vector, Vector]]:
    """Convert a Guide into world segments; ``moving_co`` sizes infinite guides."""
    if isinstance(guide, GuideLine):
        return [axis_parallel_segment(guide.point, guide.direction, moving_co)]
    if isinstance(guide, GuideSegment):
        return [(guide.a.copy(), guide.b.copy())]
    if isinstance(guide, GuideCircle):
        return circle_segments(guide.center, guide.normal, guide.radius)
    if isinstance(guide, GuidePlane):
        return plane_cross(guide.point, guide.normal)
    if isinstance(guide, GuideSpans):
        out: list[tuple[Vector, Vector]] = []
        for a, b in guide.gaps:
            out.extend(equal_span_marks(a, b, guide.axis))
        # Adjacent equal gaps share an end cap.
        return dedupe_segments(out)
    return []
