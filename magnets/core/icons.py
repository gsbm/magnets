"""Guide label icons, drawn on Blender's UI icon grid (no bpy).

One definition feeds both the viewport (tessellated to line segments and
triangles, see ``geometry``) and the landing page (``sprite``). The rules
follow Blender's icon guidelines (developer.blender.org/docs/features/
interface/icons/): a 1600-unit canvas on a 100-unit grid, a one-cell margin
(the drawing area is 100..1500), lines exactly one cell wide, white shapes
tinted at draw time, and lesser parts at lower opacity. Here the primary
tone (the selection or the result) is opaque and the secondary tone (the
reference) is drawn at ``SECONDARY_ALPHA``.

At 16 px a cell is one pixel, so straight lines sit on half cells (150,
250 ... 1450) and filled dots are 4 px across on whole cells, to fill exact
pixels. Coordinates are SVG-like: x right, y down.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

CANVAS = 1600
CELL = 100
AREA = (100, 1500)  # the drawing area (one cell of margin)
STROKE = CELL
SECONDARY_ALPHA = 0.6


@dataclass(frozen=True)
class Part:
    """One shape of an icon.

    ``kind``: "line" (open polyline), "poly" (closed polyline), "ring"
    ((cx, cy), r), "arc" ((cx, cy), r, a0, a1 in degrees, y down, clockwise
    from a0 to a1) or "dot" ((cx, cy), r, filled). ``tone``: "p" or "s".
    ``dash``: None, "dots" (one-cell dots every two cells) or "dashes".
    """

    kind: str
    tone: str
    geo: tuple
    dash: str | None = None


def _box(tone, x0, y0, x1, y1, dash=None):
    return Part("poly", tone, ((x0, y0), (x1, y0), (x1, y1), (x0, y1)), dash)


def _turn_arrow(tone, c, r, a0, a1, barb_deg=35.0):
    """An arc ending in one outer barb that runs to the drawing-area edge."""
    lo, hi = AREA[0] + STROKE / 2, AREA[1] - STROKE / 2
    cx, cy = c
    t = math.radians(a1)
    ex, ey = cx + r * math.cos(t), cy + r * math.sin(t)
    tx, ty = -math.sin(t), math.cos(t)  # travel direction at the end
    for b in (math.radians(barb_deg), -math.radians(barb_deg)):
        dx = -(tx * math.cos(b) - ty * math.sin(b))
        dy = -(ty * math.cos(b) + tx * math.sin(b))
        if dx * (ex - cx) + dy * (ey - cy) >= 0:  # the barb pointing outwards
            break
    reach = min(
        ((hi - ex) / dx if dx > 0 else (lo - ex) / dx) if dx else math.inf,
        ((hi - ey) / dy if dy > 0 else (lo - ey) / dy) if dy else math.inf,
    )
    end = (round(ex + dx * reach, 3), round(ey + dy * reach, 3))
    return (Part("arc", tone, (c, r, a0, a1)), Part("line", tone, ((ex, ey), end)))


# Icon id -> parts. Ids are guide family ids, plus "rotate" (the rotate snap
# note). Alignment has no icon: it keeps the axis letter, as Blender does.
ICONS: dict[str, tuple[Part, ...]] = {
    # The square family: an indicator on the left, the selection square on
    # the right. Two 6-cell items and a 2-cell gap fill the drawing area.
    "spacing": (  # a square, then the selection one gap further on
        _box("s", 150, 550, 650, 1050),
        _box("p", 950, 550, 1450, 1050),
    ),
    "repeat_size": (  # a gap of the object's own size (dotted), then the selection
        _box("s", 150, 550, 650, 1050, dash="dots"),
        _box("p", 950, 550, 1450, 1050),
    ),
    "equal_size": (  # "=" as wide as the square, on its top and bottom edges
        Part("line", "p", ((150, 550), (650, 550))),
        Part("line", "p", ((150, 1050), (650, 1050))),
        _box("p", 950, 550, 1450, 1050),
    ),
    "midpoint": (  # the middle of a segment
        Part("line", "s", ((150, 750), (1450, 750))),
        Part("line", "s", ((150, 550), (150, 950))),
        Part("line", "s", ((1450, 550), (1450, 950))),
        Part("poly", "p", ((800, 400), (1150, 750), (800, 1100), (450, 750))),
    ),
    "tangency": (  # Surface Contact: a square resting on a surface
        Part("line", "s", ((150, 1450), (1450, 1450))),
        _box("p", 450, 650, 1150, 1350),
    ),
    "sphere_tangency": (  # two circles touching at one point
        Part("ring", "s", ((550, 750), 400)),
        Part("ring", "p", ((1200, 750), 250)),
    ),
    "concentric": (  # two rings sharing one center
        Part("ring", "s", ((800, 800), 650)),
        Part("ring", "p", ((800, 800), 350)),
    ),
    "parallel": (  # two parallel edges
        Part("line", "s", ((150, 1050), (1050, 150))),
        Part("line", "p", ((550, 1450), (1450, 550))),
    ),
    "collinear": (  # a point on the line that continues an edge
        Part("line", "s", ((150, 1450), (650, 950))),
        Part("line", "s", ((650, 950), (1050, 550)), dash="dots"),
        Part("dot", "p", ((1300, 300), 200)),
    ),
    "coplanar": (  # a point on the plane of a face
        Part("poly", "s", ((150, 1150), (550, 450), (1450, 450), (1050, 1150))),
        Part("dot", "p", ((800, 800), 200)),
    ),
    "symmetry": (  # a point mirrored across a plane
        Part("line", "s", ((750, 150), (750, 1450)), dash="dashes"),
        Part("poly", "s", ((550, 450), (550, 1150), (150, 800))),
        Part("poly", "p", ((950, 450), (950, 1150), (1350, 800))),
    ),
    "rotate": (  # a turn around a pivot
        *_turn_arrow("p", (800, 800), 550, -160, 80),
        Part("dot", "s", ((800, 800), 200)),
    ),
}


def icon_for_family(family: str) -> str | None:
    """The icon id for a guide family, or None (alignment keeps its letter)."""
    return family if family in ICONS else None


# ── Sampling ─────────────────────────────────────────────────────────────────


def _circle_points(c, r, a0, a1, step_units=60.0) -> list[tuple[float, float]]:
    """Points along an arc from a0 to a1 (degrees, y down)."""
    sweep = a1 - a0
    n = max(8, int(abs(math.radians(sweep)) * r / step_units))
    cx, cy = c
    return [
        (cx + r * math.cos(math.radians(a0 + sweep * i / n)),
         cy + r * math.sin(math.radians(a0 + sweep * i / n)))
        for i in range(n + 1)
    ]


def _path(part: Part) -> tuple[list[tuple[float, float]], bool]:
    """Centerline points of a stroked part and whether it is closed."""
    if part.kind == "line":
        return list(part.geo), False
    if part.kind == "poly":
        return list(part.geo), True
    if part.kind == "ring":
        (c, r) = part.geo
        return _circle_points(c, r, 0.0, 360.0)[:-1], True
    if part.kind == "arc":
        c, r, a0, a1 = part.geo
        return _circle_points(c, r, a0, a1), False
    raise ValueError(part.kind)


def _walk(points, closed):
    """Yield the path's segments with their start distance along it."""
    pts = list(points) + ([points[0]] if closed else [])
    dist = 0.0
    for a, b in pairwise(pts):
        length = math.dist(a, b)
        yield a, b, dist, length
        dist += length


def _point_at(points, closed, s):
    for a, b, d, length in _walk(points, closed):
        if d <= s <= d + length and length > 0:
            t = (s - d) / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    return None


def _total(points, closed):
    return sum(length for *_ab, _d, length in _walk(points, closed))


def _sub_path(points, closed, s0, s1):
    """The piece of the path between distances s0 and s1."""
    out = [_point_at(points, closed, s0)]
    for a, b, d, length in _walk(points, closed):
        if s0 < d + length < s1:
            out.append(b)
    out.append(_point_at(points, closed, s1))
    return [p for p in out if p is not None]


def _pieces(part: Part):
    """(strokes, dots): stroked polylines and filled circles, in icon units."""
    if part.kind == "dot":
        return [], [part.geo]
    points, closed = _path(part)
    if part.dash is None:
        return [points + ([points[0]] if closed else [])], []
    total = _total(points, closed)
    if part.dash == "dots":  # one-cell round dots every two cells
        n = int(total // (2 * CELL) + 1e-9)
        dots = [(_point_at(points, closed, i * 2 * CELL), STROKE / 2) for i in range(n + (0 if closed else 1))]
        return [], [(p, r) for p, r in dots if p is not None]
    if part.dash == "dashes":  # one-cell dash every three cells, round caps
        strokes, s = [], 0.0
        while s < total:
            strokes.append(_sub_path(points, closed, max(0.0, s - STROKE / 2), min(total, s + 1.5 * STROKE)))
            s += 3 * CELL
        return strokes, []
    raise ValueError(part.dash)


# ── Viewport geometry ────────────────────────────────────────────────────────


def geometry(icon_id: str, x: float, y: float, size: float):
    """Screen geometry of an icon in a ``size`` px box whose bottom-left is (x, y).

    Returns ``(lines, fills, width)``: ``lines`` maps a tone to line-segment
    endpoint pairs (y up, as in region pixels), ``fills`` maps a tone to
    triangle vertices, and ``width`` is the stroke width in px.
    """
    k = size / CANVAS

    def px(p):
        return (x + p[0] * k, y + size - p[1] * k)

    lines: dict[str, list] = {"p": [], "s": []}
    fills: dict[str, list] = {"p": [], "s": []}
    for part in ICONS[icon_id]:
        strokes, dots = _pieces(part)
        for poly in strokes:
            for a, b in pairwise(poly):
                lines[part.tone] += [px(a), px(b)]
        for (cx, cy), r in dots:
            c = px((cx, cy))
            rr = r * k
            n = 16
            ring = [(c[0] + rr * math.cos(2 * math.pi * i / n), c[1] + rr * math.sin(2 * math.pi * i / n))
                    for i in range(n)]
            for i in range(n):
                fills[part.tone] += [c, ring[i], ring[(i + 1) % n]]
    return lines, fills, STROKE * k


# ── SVG (landing page) ───────────────────────────────────────────────────────


def _num(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def _svg_part(part: Part) -> str:
    op = "" if part.tone == "p" else f' opacity="{SECONDARY_ALPHA}"'
    dash = {None: "", "dots": ' stroke-dasharray="0 200"', "dashes": ' stroke-dasharray="100 200"'}[part.dash]
    stroke = (f'fill="none" stroke="currentColor" stroke-width="{STROKE}" '
              f'stroke-linecap="round" stroke-linejoin="round"{dash}{op}')
    if part.kind in ("line", "poly"):
        tag = "polyline" if part.kind == "line" else "polygon"
        pts = " ".join(f"{_num(px)},{_num(py)}" for px, py in part.geo)
        return f'<{tag} points="{pts}" {stroke}/>'
    if part.kind == "ring":
        (cx, cy), r = part.geo
        return f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" {stroke}/>'
    if part.kind == "dot":
        (cx, cy), r = part.geo
        return f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" fill="currentColor"{op}/>'
    if part.kind == "arc":
        (cx, cy), r, a0, a1 = part.geo
        p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
        p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
        large = 1 if (a1 - a0) % 360 > 180 else 0
        return (f'<path d="M{_num(p0[0])} {_num(p0[1])}A{_num(r)} {_num(r)} 0 {large} 1 '
                f'{_num(p1[0])} {_num(p1[1])}" {stroke}/>')
    raise ValueError(part.kind)


def sprite() -> str:
    """An SVG sprite with one ``<symbol id="i-<icon id>">`` per icon."""
    symbols = "\n".join(
        f'  <symbol id="i-{icon_id}" viewBox="0 0 {CANVAS} {CANVAS}">'
        f'{"".join(_svg_part(p) for p in parts)}</symbol>'
        for icon_id, parts in ICONS.items()
    )
    return (
        "<!-- Generated from magnets/core/icons.py by build/export_icons.py; do not edit. -->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg">\n{symbols}\n</svg>\n'
    )
