"""Release-time snap math for rotate/scale and perf throttle."""

from __future__ import annotations

import math

from mathutils import Matrix, Vector


def snap_rotation_delta(
    start_mw: Matrix,
    final_mw: Matrix,
    increment_deg: float,
    *,
    window_frac: float = 0.34,
) -> tuple[Vector, float] | None:
    """Angle-increment snap for a rotate.

    Returns ``(axis, total_angle)``: the rotation to apply to the *start*
    orientation so the net rotation lands exactly on the nearest multiple of
    ``increment_deg``, or ``None`` when no snap should occur:

    * increment disabled, or the net rotation is ~0,
    * the nearest multiple is 0 (no meaningful snap target),
    * the native angle is farther than ``window_frac × increment`` from the
      nearest multiple (a deliberate off-increment angle),
    * the angle is already exactly on the increment (nothing to correct).
    """
    if increment_deg <= 1e-6:
        return None
    q_delta = final_mw.to_quaternion() @ start_mw.to_quaternion().inverted()
    q_delta.normalize()
    angle = q_delta.angle  # 0..pi
    if angle < 1e-6:
        return None
    axis = q_delta.axis
    if axis.length_squared < 1e-12:
        return None
    inc = math.radians(increment_deg)
    nearest = round(angle / inc) * inc
    if nearest < 1e-9:
        return None
    if abs(angle - nearest) > inc * window_frac:
        return None
    # Already on the increment (within float round-trip noise ~ 0.006°): nothing
    # worth committing an undo step for.
    if abs(angle - nearest) < 1e-4:
        return None
    return axis.normalized(), nearest


def nearest_size_match(
    current_dim: float,
    candidates: list[tuple[str, float]],
    world_tol: float,
) -> tuple[str, float, float] | None:
    """Return ``(name, size, factor)`` for the nearest neighbour size, or None.

    ``factor`` scales ``current_dim`` onto that size. None when nothing is
    within ``world_tol`` or the sizes already match exactly.
    """
    if current_dim <= 1e-9 or world_tol <= 0.0 or not candidates:
        return None
    best = None
    best_gap = world_tol
    for name, dim in candidates:
        if dim <= 1e-9:
            continue
        gap = abs(current_dim - dim)
        if gap <= best_gap:
            best_gap = gap
            best = (name, dim)
    if best is None:
        return None
    factor = best[1] / current_dim
    if abs(factor - 1.0) < 1e-9:
        return None
    return best[0], best[1], factor


def equal_size_scale(
    current_dim: float,
    candidate_dims: list[float],
    world_tol: float,
) -> float | None:
    """Return the factor of ``nearest_size_match`` for bare sizes, or None."""
    match = nearest_size_match(
        current_dim, [("", d) for d in candidate_dims], world_tol
    )
    return match[2] if match is not None else None


def rotated_matrix(
    matrix: Matrix, axis: Vector, angle: float, pivot: Vector
) -> Matrix:
    """Return ``matrix`` rotated by ``angle`` about ``axis`` through ``pivot``."""
    rot = Matrix.Rotation(angle, 4, axis.normalized())
    # Rotate the basis first (rot @ matrix), then set the pivot-correct origin.
    # Order matters: doing it the other way round rotates the translation twice.
    out = rot @ matrix
    out.translation = pivot + rot @ (matrix.translation - pivot)
    return out


def scaled_matrix(matrix: Matrix, factor: float, pivot: Vector) -> Matrix:
    """Return ``matrix`` uniformly scaled by ``factor`` about ``pivot``.

    Equivalent to ``T(pivot) @ S(factor) @ T(-pivot) @ matrix``.
    """
    basis = matrix.copy()
    basis.translation = Vector((0.0, 0.0, 0.0))
    out = Matrix.Scale(factor, 4) @ basis
    out.translation = pivot + (matrix.translation - pivot) * factor
    return out


def adaptive_interval(
    last_infer_s: float,
    *,
    base: float,
    budget_s: float = 0.008,
    ceiling_s: float = 0.1,
    slack: float = 1.5,
) -> float:
    """Return the next timer delay given the last inference cost.

    ``base`` while within ``budget_s``; otherwise ``last_infer_s * slack``,
    capped at ``ceiling_s``.
    """
    if last_infer_s <= budget_s:
        return base
    return min(max(base, last_infer_s * slack), ceiling_s)
