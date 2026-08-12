"""Shared geometry helpers (no bpy)."""

from __future__ import annotations

from mathutils import Vector


def normalize(v: Vector) -> Vector:
    """Return a unit vector, or +Z if ``v`` is zero-length."""
    if v.length_squared == 0.0:
        return Vector((0.0, 0.0, 1.0))
    return v.normalized()


def project_point_on_line(point: Vector, line_point: Vector, direction: Vector) -> Vector:
    """Orthogonal projection of ``point`` onto the infinite line.

    Args:
        point: Query point.
        line_point: A point on the line.
        direction: Line direction (need not be unit length).

    Returns:
        Closest point on the line to ``point``.
    """
    d = normalize(direction)
    t = (point - line_point).dot(d)
    return line_point + d * t


def distance_point_line(point: Vector, line_point: Vector, direction: Vector) -> float:
    """Distance from ``point`` to the infinite line.

    Args:
        point: Query point.
        line_point: A point on the line.
        direction: Line direction.

    Returns:
        Non-negative distance.
    """
    proj = project_point_on_line(point, line_point, direction)
    return (point - proj).length


def distance_point_plane(point: Vector, plane_point: Vector, normal: Vector) -> float:
    """Absolute distance from ``point`` to the plane.

    Args:
        point: Query point.
        plane_point: A point on the plane.
        normal: Plane normal.

    Returns:
        Non-negative distance.
    """
    n = normalize(normal)
    return abs((point - plane_point).dot(n))


def reflect_point(point: Vector, plane_point: Vector, normal: Vector) -> Vector:
    """Reflect ``point`` across the plane.

    Args:
        point: Point to reflect.
        plane_point: A point on the plane.
        normal: Plane normal.

    Returns:
        Reflected point.
    """
    n = normalize(normal)
    d = (point - plane_point).dot(n)
    return point - 2.0 * d * n


def lines_parallel(dir_a: Vector, dir_b: Vector, angle_tol: float = 0.05) -> bool:
    """True if directions are parallel within tolerance.

    Args:
        dir_a: First direction.
        dir_b: Second direction.
        angle_tol: Allowed deviation from |dot| == 1.

    Returns:
        Whether the directions are parallel.
    """
    a = normalize(dir_a)
    b = normalize(dir_b)
    return abs(abs(a.dot(b)) - 1.0) <= angle_tol


def lines_perpendicular(dir_a: Vector, dir_b: Vector, angle_tol: float = 0.05) -> bool:
    """True if directions are perpendicular within tolerance.

    Args:
        dir_a: First direction.
        dir_b: Second direction.
        angle_tol: Allowed |dot| threshold.

    Returns:
        Whether the directions are perpendicular.
    """
    return abs(normalize(dir_a).dot(normalize(dir_b))) <= angle_tol


def collinear(a: Vector, b: Vector, c: Vector, tol: float) -> bool:
    """True if ``c`` lies within ``tol`` of the line through ``a`` and ``b``.

    Args:
        a: First line point.
        b: Second line point.
        c: Query point.
        tol: Maximum perpendicular distance.

    Returns:
        Whether the three points are collinear within tolerance.
    """
    ab = b - a
    if ab.length_squared <= tol * tol:
        return True
    perp = (c - a) - ab.normalized() * (c - a).dot(ab.normalized())
    return perp.length <= tol
