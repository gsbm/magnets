"""Resolve one or more constraint deltas into a transform offset."""

from __future__ import annotations

import math

from mathutils import Vector

from .frames import Frame
from .graph import constraints_compatible, snap_axis_slot
from .relationship import Relationship


def resolve_translation(
    active: list[Relationship],
    frame: Frame = Frame.WORLD,
) -> Vector:
    """Merge active translation constraints into one world-space offset.

    Args:
        active: Ranked relationships currently engaged.
        frame: Unused; retained for call-site compatibility.

    Returns:
        Combined translation vector.
    """
    del frame
    if not active:
        return Vector((0.0, 0.0, 0.0))
    if len(active) == 1:
        return active[0].delta.translation.copy()

    ordered = sorted(active, key=lambda r: -r.base_priority)
    result = Vector((0.0, 0.0, 0.0))
    accepted: list[Relationship] = []
    used_slots: set[str] = set()

    for rel in ordered:
        slot = snap_axis_slot(rel)
        if slot in used_slots:
            continue
        if accepted and not all(constraints_compatible(rel, prev) for prev in accepted):
            continue
        result += rel.delta.translation
        accepted.append(rel)
        used_slots.add(slot)
    return result


def resolve_rotation(
    active: list[Relationship],
    *,
    angle_snap_deg: float = 0.0,
) -> tuple[Vector, float]:
    """Pick a rotation correction from active relationships.

    Args:
        active: Engaged relationships.
        angle_snap_deg: Optional discrete angle increment in degrees.

    Returns:
        ``(axis, angle_radians)``. Defaults to ``(+Z, 0)`` when none apply.
    """
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
    """Pick per-axis scale factors from active relationships.

    Args:
        active: Engaged relationships.

    Returns:
        Scale factors. Uniform when only ``scale_factor`` is set.
    """
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
    """Quantize ``angle`` (radians) to the nearest ``increment_deg`` step.

    Args:
        angle: Angle in radians.
        increment_deg: Step size in degrees.

    Returns:
        Quantized angle in radians.
    """
    if increment_deg <= 1e-6:
        return angle
    inc = math.radians(increment_deg)
    return round(angle / inc) * inc


def clamp_translation_step(correction: Vector, max_length: float) -> Vector:
    """Clamp ``correction`` length to ``max_length``.

    Args:
        correction: Translation delta.
        max_length: Maximum allowed length (no-op if <= 0).

    Returns:
        Possibly shortened correction vector.
    """
    if max_length <= 0.0:
        return correction
    limit_sq = max_length * max_length
    if correction.length_squared <= limit_sq:
        return correction
    return correction.normalized() * max_length
