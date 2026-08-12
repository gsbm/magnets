"""Relationship compatibility and active constraint sets."""

from __future__ import annotations

from .relationship import Relationship
from .scoring import RankItem


def snap_axis_slot(rel: Relationship) -> str:
    """Return the exclusivity slot for ``rel`` (one engaged guide per slot).

    Orthogonal axes (e.g. ``alignment:X`` vs ``alignment:Y``) use different
    slots and may compose.
    """
    if rel.family == "alignment":
        return f"alignment:{rel.axis}"
    return f"{rel.family}:{rel.axis}"


def constraints_compatible(a: Relationship, b: Relationship) -> bool:
    """Return True if two relationships may be satisfied together.

    Args:
        a: First relationship.
        b: Second relationship.

    Returns:
        Compatibility flag.
    """
    if snap_axis_slot(a) == snap_axis_slot(b):
        return False
    if a.family == "alignment" and b.family == "alignment":
        return a.axis != b.axis
    if a.family == b.family and a.axis == b.axis:
        return False
    # Orthogonal translation families generally compose.
    if a.family in {"alignment", "midpoint", "spacing", "symmetry", "collinear", "coplanar"}:
        if b.family in {"alignment", "midpoint", "spacing", "symmetry", "collinear", "coplanar"}:
            return True
    return a.family == b.family


def build_active_set(
    primary: RankItem,
    ranked: list[RankItem],
    *,
    snap_px: float,
    release_px: float | None = None,
    max_constraints: int = 3,
    visible: list[RankItem] | None = None,
    sticky_keys: set[tuple] | None = None,
) -> list[Relationship]:
    """Build the engaged constraint set from a ranked candidate list.

    Args:
        primary: Highest-priority guide currently within snap range.
        ranked: Score-sorted candidates (skip out-of-range; do not break early).
        snap_px: Engage distance for new secondary guides.
        release_px: Hold distance for already-latched guides (hysteresis).
        max_constraints: Cap on simultaneous constraints.
        visible: Optional wider pool for sticky re-attachment.
        sticky_keys: Keys previously latched that may re-attach within
            ``release_px``.

    Returns:
        Compatible relationships including ``primary``.
    """
    hold_px = release_px if release_px is not None else snap_px
    selected: list[Relationship] = [primary.payload]
    used_keys: set[tuple] = {primary.key}
    used_slots: set[str] = {snap_axis_slot(primary.payload)}

    def try_add(item: RankItem, max_dist: float) -> bool:
        if item.key in used_keys:
            return False
        if item.screen_dist > max_dist:
            return False
        if len(selected) >= max_constraints:
            return False
        slot = snap_axis_slot(item.payload)
        if slot in used_slots:
            return False
        if not all(constraints_compatible(item.payload, existing) for existing in selected):
            return False
        selected.append(item.payload)
        used_keys.add(item.key)
        used_slots.add(slot)
        return True

    # New secondaries use snap_px; release_px is only for already-latched holds.
    for item in ranked:
        if item.key == primary.key:
            continue
        try_add(item, snap_px)

    if sticky_keys and visible:
        for item in visible:
            if item.key not in sticky_keys:
                continue
            try_add(item, hold_px)

    return selected
