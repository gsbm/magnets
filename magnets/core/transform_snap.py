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
    """Equal-size snap target for a scale, with the neighbour it matches.

    Args:
        current_dim: The object's current overall size (largest bbox dim).
        candidates: ``(name, size)`` of nearby objects.
        world_tol: Largest size difference that still snaps.

    Returns:
        ``(name, size, factor)`` where ``factor`` scales the *current* size
        onto the nearest candidate, or None when nothing is close enough (or
        the sizes already match exactly).
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
    """Equal-size snap factor for a scale (see ``nearest_size_match``).

    Given the object's current overall size (``current_dim``, e.g. its largest
    world bounding-box dimension) and the sizes of nearby objects, return the
    uniform factor to apply to the *current* scale so the size matches the
    nearest candidate within ``world_tol``, or ``None`` if nothing is close
    enough (or the match is already exact).
    """
    match = nearest_size_match(
        current_dim, [("", d) for d in candidate_dims], world_tol
    )
    return match[2] if match is not None else None


def rotated_matrix(
    matrix: Matrix, axis: Vector, angle: float, pivot: Vector
) -> Matrix:
    """World matrix rotated by ``angle`` about ``axis`` around ``pivot``.

    Mirrors ``ops.pipeline.apply_object_rotation`` without mutating an object,
    so the commit can compute a final pose to hand to the undo-collapse.
    """
    rot = Matrix.Rotation(angle, 4, axis.normalized())
    # Rotate the basis first (rot @ matrix), then set the pivot-correct origin.
    # Order matters: doing it the other way round rotates the translation twice.
    out = rot @ matrix
    out.translation = pivot + rot @ (matrix.translation - pivot)
    return out


def scaled_matrix(matrix: Matrix, factor: float, pivot: Vector) -> Matrix:
    """World matrix uniformly scaled by ``factor`` about ``pivot``.

    Scales the basis (so the object's ``scale`` channel changes when the matrix
    is assigned) and moves the origin relative to the pivot. Equivalent to
    ``T(pivot) @ Scale(factor) @ T(-pivot) @ matrix`` for a uniform factor.
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
    """Compute the next timer delay from the previous inference cost.

    Args:
        last_infer_s: Duration of the last inference tick in seconds.
        base: Default interval when under budget.
        budget_s: Cost threshold before backing off.
        ceiling_s: Maximum interval.
        slack: Multiplier applied to ``last_infer_s`` when over budget.

    Returns:
        Seconds until the next timer fire.
    """
    if last_infer_s <= budget_s:
        return base
    return min(max(base, last_infer_s * slack), ceiling_s)
