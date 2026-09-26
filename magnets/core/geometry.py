"""Shared geometry helpers (no bpy)."""

from __future__ import annotations

from mathutils import Vector


def normalize(v: Vector) -> Vector:
    """Return a unit vector, or +Z if ``v`` is zero-length."""
    if v.length_squared == 0.0:
        return Vector((0.0, 0.0, 1.0))
    return v.normalized()


def project_point_on_line(point: Vector, line_point: Vector, direction: Vector) -> Vector:
    """Project ``point`` onto the infinite line (``direction`` need not be unit)."""
    d = normalize(direction)
    t = (point - line_point).dot(d)
    return line_point + d * t


def distance_point_line(point: Vector, line_point: Vector, direction: Vector) -> float:
    """Return the distance from ``point`` to the infinite line."""
    proj = project_point_on_line(point, line_point, direction)
    return (point - proj).length


def distance_point_plane(point: Vector, plane_point: Vector, normal: Vector) -> float:
    """Return the absolute distance from ``point`` to the plane."""
    n = normalize(normal)
    return abs((point - plane_point).dot(n))


def reflect_point(point: Vector, plane_point: Vector, normal: Vector) -> Vector:
    """Reflect ``point`` across the plane."""
    n = normalize(normal)
    d = (point - plane_point).dot(n)
    return point - 2.0 * d * n


def lines_parallel(dir_a: Vector, dir_b: Vector, angle_tol: float = 0.05) -> bool:
    """Return True if ``abs(|dot| - 1) <= angle_tol`` for the two directions."""
    a = normalize(dir_a)
    b = normalize(dir_b)
    return abs(abs(a.dot(b)) - 1.0) <= angle_tol


def lines_perpendicular(dir_a: Vector, dir_b: Vector, angle_tol: float = 0.05) -> bool:
    """Return True if the directions are perpendicular (``|dot| <= angle_tol``)."""
    return abs(normalize(dir_a).dot(normalize(dir_b))) <= angle_tol


def collinear(a: Vector, b: Vector, c: Vector, tol: float) -> bool:
    """Return True if ``c`` is within ``tol`` of the line through ``a`` and ``b``."""
    ab = b - a
    if ab.length_squared <= tol * tol:
        return True
    perp = (c - a) - ab.normalized() * (c - a).dot(ab.normalized())
    return perp.length <= tol
