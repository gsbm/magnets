"""Bounding-box geometry helpers (no bpy)."""

from __future__ import annotations

from mathutils import Vector

_FACE_CORNER_GROUPS = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (0, 1, 4, 5),
    (2, 3, 6, 7),
    (0, 2, 4, 6),
    (1, 3, 5, 7),
)

_EDGE_PAIRS = (
    (0, 1),
    (0, 2),
    (0, 4),
    (1, 3),
    (1, 5),
    (2, 3),
    (2, 6),
    (3, 7),
    (4, 5),
    (4, 6),
    (5, 7),
    (6, 7),
)


def bbox_face_centers(corners: list[Vector]) -> list[Vector]:
    """Return the six face-center points of an 8-corner box."""
    if len(corners) < 8:
        return []
    out: list[Vector] = []
    for group in _FACE_CORNER_GROUPS:
        pts = [corners[i] for i in group]
        out.append(sum(pts, Vector()) / len(pts))
    return out


def bbox_centroid(corners: list[Vector]) -> Vector | None:
    """Return the mean of ``corners``, or None if empty."""
    if not corners:
        return None
    return sum(corners, Vector()) / len(corners)


def bbox_edges(corners: list[Vector]) -> list[tuple[Vector, Vector]]:
    """Return the twelve edges of an 8-corner box."""
    if len(corners) < 8:
        return []
    return [(corners[a].copy(), corners[b].copy()) for a, b in _EDGE_PAIRS]


def bbox_face_planes(corners: list[Vector]) -> list[tuple[Vector, Vector]]:
    """Face center and outward normal (local space)."""
    if len(corners) < 8:
        return []
    out: list[tuple[Vector, Vector]] = []
    for group in _FACE_CORNER_GROUPS:
        pts = [corners[i] for i in group]
        center = sum(pts, Vector()) / len(pts)
        u = pts[1] - pts[0]
        v = pts[2] - pts[0]
        normal = u.cross(v)
        if normal.length_squared == 0.0:
            continue
        out.append((center, normal.normalized()))
    return out


def bbox_dimensions(corners: list[Vector]) -> Vector | None:
    """Return XYZ extents of ``corners``, or None."""
    if len(corners) < 8:
        return None
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return Vector((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))


def bbox_bounding_sphere(corners: list[Vector]) -> tuple[Vector, float] | None:
    """Return ``(centroid, radius)`` covering ``corners``."""
    centroid = bbox_centroid(corners)
    if centroid is None:
        return None
    radius = max((c - centroid).length for c in corners)
    return centroid, radius
