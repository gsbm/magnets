"""Resolve one or more constraint deltas into a transform offset."""

from __future__ import annotations

import math

from mathutils import Vector

from .frames import Frame
from .graph import constraints_compatible, snap_axis_slot
from .relationship import Relationship

# Which relationship wins an axis when several engage at once: alignment is the
# primary smart-guide snap, plane/line contact next, distribution-style guides
# last. Families not listed rank after these, in input order.
FAMILY_PRIORITY: tuple[str, ...] = (
    "alignment",
    "coplanar",
    "collinear",
    "symmetry",
    "spacing",
    "repeat_size",
    "midpoint",
)
_FAMILY_RANK = {family: i for i, family in enumerate(FAMILY_PRIORITY)}

# Components below this (world units) count as "nothing left to apply".
_EPS = 1e-9


def _family_rank(rel: Relationship) -> int:
    return _FAMILY_RANK.get(rel.family, len(FAMILY_PRIORITY))


def _project_off(vec: Vector, basis: list[Vector]) -> Vector:
    """``vec`` minus its components along each (orthonormal) basis vector."""
    out = vec.copy()
    for u in basis:
        out -= u * out.dot(u)
    return out


def _claim(basis: list[Vector], direction: Vector | None) -> None:
    """Add ``direction``'s part orthogonal to ``basis`` as a new basis vector."""
    if direction is None:
        return
    rest = _project_off(direction, basis)
    if rest.length > 1e-6:
        basis.append(rest.normalized())


def resolve_translation(
    active: list[Relationship],
    frame: Frame = Frame.WORLD,
) -> Vector:
    """Merge active translation constraints into one world-space offset.

    Relationships are taken in family priority order, and each delta is
    projected off the directions already claimed (Gram-Schmidt): orthogonal
    constraints add, overlapping ones do not stack. A satisfied constraint
    still claims its ``constraint_dir``, so a lower-priority guide cannot pull
    the selection off it. ``frame`` is unused.
    """
    del frame
    if not active:
        return Vector((0.0, 0.0, 0.0))
    if len(active) == 1:
        return active[0].delta.translation.copy()

    # sorted() is stable: equal keys keep their ranked (input) order.
    ordered = sorted(active, key=lambda r: (_family_rank(r), -r.base_priority))
    result = Vector((0.0, 0.0, 0.0))
    claimed: list[Vector] = []  # orthonormal directions already corrected
    accepted: list[Relationship] = []
    used_slots: set[str] = set()
    for rel in ordered:
        slot = snap_axis_slot(rel)
        if slot in used_slots:
            continue
        if accepted and not all(constraints_compatible(rel, prev) for prev in accepted):
            continue
        accepted.append(rel)
        used_slots.add(slot)

        applied = _project_off(rel.delta.translation, claimed)
        if applied.length > _EPS:
            result += applied
        if rel.constraint_dir is not None:
            _claim(claimed, rel.constraint_dir)
        elif applied.length > _EPS:
            _claim(claimed, applied)
    return result


def resolve_rotation(
    active: list[Relationship],
    *,
    angle_snap_deg: float = 0.0,
) -> tuple[Vector, float]:
    """Return ``(axis, angle_radians)`` from active relationships, or ``(+Z, 0)``."""
    if not active:
        return Vector((0.0, 0.0, 1.0)), 0.0
    for rel in active:
        if rel.delta.rotation_angle != 0.0:
            axis = rel.delta.rotation_axis.copy()
            angle = rel.delta.rotation_angle
            if angle_snap_deg > 1e-6:
                angle = snap_angle(angle, angle_snap_deg)
            return axis, angle
    return Vector((0.0, 0.0, 1.0)), 0.0


def resolve_scale(active: list[Relationship]) -> Vector:
    """Return per-axis scale factors; uniform when only ``scale_factor`` is set."""
    if not active:
        return Vector((1.0, 1.0, 1.0))
    for rel in active:
        sf = rel.delta.scale_factor
        if abs(sf - 1.0) > 1e-9:
            return Vector((sf, sf, sf))
        if rel.delta.scale_axis.length_squared > 0.0:
            return rel.delta.scale_axis.copy()
    return Vector((1.0, 1.0, 1.0))


def snap_angle(angle: float, increment_deg: float) -> float:
    """Quantize ``angle`` (radians) to the nearest ``increment_deg`` step."""
    if increment_deg <= 1e-6:
        return angle
    inc = math.radians(increment_deg)
    return round(angle / inc) * inc


def clamp_translation_step(correction: Vector, max_length: float) -> Vector:
    """Clamp ``correction`` to ``max_length`` (no-op when ``max_length <= 0``)."""
    if max_length <= 0.0:
        return correction
    limit_sq = max_length * max_length
    if correction.length_squared <= limit_sq:
        return correction
    return correction.normalized() * max_length
