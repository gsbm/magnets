"""Glyph geometry helpers (mathutils only)."""

from __future__ import annotations

import math

from mathutils import Vector

# ── World-space guide geometry ─────────────────────────────────────────────────

def dash_segments(
    a: Vector,
    b: Vector,
    dash: float = 0.12,
    gap: float = 0.08,
    max_count: int | None = None,
):
    """Return dashed world-space segments along a→b.

    Args:
        a: Segment start.
        b: Segment end.
        dash: Dash length.
        gap: Gap length.
        max_count: Optional cap on the dash count; beyond it dash and gap
            grow proportionally so a very long line stays cheap to draw.

    Returns:
        List of ``(p0, p1)`` pairs.
    """
    ab = b - a
    length = ab.length
    if length == 0.0 or dash <= 0.0:
        return []
    direction = ab / length
    step = dash + gap
    if max_count and length / step > max_count:
        grow = length / (step * max_count)
        dash *= grow
        step *= grow
    out = []
    t = 0.0
    while t < length:
        p0 = a + direction * t
        p1 = a + direction * min(t + dash, length)
        out.append((p0, p1))
        t += step
    return out


def extend_segment(a: Vector, b: Vector, margin: float = 0.2):
    """Extend a→b by ``margin`` fraction on each side.

    Args:
        a: Segment start.
        b: Segment end.
        margin: Fractional extension.

    Returns:
        Extended ``(p0, p1)``.
    """
    d = b - a
    return (a - d * margin, b + d * margin)


def axis_parallel_segment(
    anchor: Vector,
    direction: Vector,
    extent_point: Vector,
    margin: float = 0.25,
):
    """Build a segment along ``direction`` through ``anchor``.

    Args:
        anchor: Point on the guide axis.
        direction: Guide direction.
        extent_point: Point used to size the segment.
        margin: Fractional extension.

    Returns:
        ``(p0, p1)`` endpoints.
    """
    if direction.length_squared == 0.0:
        return (anchor.copy(), anchor.copy())
    d = direction.normalized()
    t = d.dot(extent_point - anchor)
    dvec = anchor + d * t - anchor
    a = anchor - dvec * margin
    b = anchor + d * t + dvec * margin
    return (a, b)


def _perpendicular_unit(direction: Vector) -> Vector:
    d = direction.normalized()
    helper = Vector((0.0, 0.0, 1.0))
    if abs(d.dot(helper)) > 0.95:
        helper = Vector((0.0, 1.0, 0.0))
    return d.cross(helper).normalized()


def endpoint_ticks(
    point: Vector,
    direction: Vector,
    size: float = 0.08,
) -> tuple[tuple[Vector, Vector], tuple[Vector, Vector]]:
    """Perpendicular tick marks at a segment endpoint.

    Args:
        point: Tick center.
        direction: Guide direction.
        size: Tick length.

    Returns:
        Tick segment endpoints.
    """
    n = _perpendicular_unit(direction)
    half = size * 0.5
    a = point - n * half
    b = point + n * half
    return (a, b)


def guide_ticks(
    anchor: Vector,
    extent: Vector,
    direction: Vector,
    size: float = 0.08,
) -> list[tuple[Vector, Vector]]:
    """Tick marks along a guide segment.

    Args:
        anchor: Guide anchor.
        extent: Extent point.
        direction: Guide direction.
        size: Tick size.

    Returns:
        List of tick segments.
    """
    return [endpoint_ticks(anchor, direction, size), endpoint_ticks(extent, direction, size)]


# ── Screen-space dot / marker geometry ────────────────────────────────────────

def circle_2d_verts(
    cx: float,
    cy: float,
    radius: float,
    segments: int = 20,
) -> list[tuple[float, float]]:
    """Return screen-space (x, y) vertices forming a circle outline (LINE_LOOP).

    Caller is responsible for splitting into LINE pairs if needed.
    """
    verts = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        verts.append((cx + math.cos(ang) * radius, cy + math.sin(ang) * radius))
    return verts


def circle_2d_line_pairs(
    cx: float,
    cy: float,
    radius: float,
    segments: int = 20,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Return consecutive screen-space pairs outlining a circle.

    Args:
        cx: Center X in pixels.
        cy: Center Y in pixels.
        radius: Radius in pixels.
        segments: Number of segments.

    Returns:
        List of ``((x0, y0), (x1, y1))`` pairs.
    """
    verts = circle_2d_verts(cx, cy, radius, segments)
    pairs = []
    n = len(verts)
    for i in range(n):
        pairs.append((verts[i], verts[(i + 1) % n]))
    return pairs


def square_2d_verts(
    cx: float,
    cy: float,
    half: float,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Return four screen-space corners of an axis-aligned square.

    Args:
        cx: Center X.
        cy: Center Y.
        half: Half side length.

    Returns:
        Tuple of four ``(x, y)`` corners.
    """
    tl = (cx - half, cy + half)
    tr = (cx + half, cy + half)
    br = (cx + half, cy - half)
    bl = (cx - half, cy - half)
    return [(tl, tr), (tr, br), (br, bl), (bl, tl)]


def crosshair_2d_verts(
    cx: float,
    cy: float,
    half: float,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Return screen-space crosshair line pairs.

    Args:
        cx: Center X.
        cy: Center Y.
        half: Half arm length.

    Returns:
        Horizontal and vertical segment pairs.
    """
    return [
        ((cx - half, cy), (cx + half, cy)),
        ((cx, cy - half), (cx, cy + half)),
    ]
