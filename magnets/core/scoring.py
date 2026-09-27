"""Score, rank, and suppress overlapping guide candidates.

Screen-space distances are supplied by adapters. The score combines family
priority, feature priority, screen proximity, and residual tightness.
"""

from __future__ import annotations

from dataclasses import dataclass

from .relationship import Relationship

# Higher values win when candidates compete. Alignment outranks spacing, etc.
FAMILY_PRIORITY = {
    "alignment": 100,
    "spacing": 90,
    "equal_size": 85,
    "midpoint": 88,
    "tangency": 82,
    "parallel": 80,
    "perpendicular": 80,
    "collinear": 78,
    "coplanar": 78,
    "concentric": 86,
    "symmetry": 84,
}

_TYPE_WEIGHT = 1000
_FEATURE_WEIGHT = 10
_SCREEN_WEIGHT = 100
_RESIDUAL_WEIGHT = 50


def relationship_score(
    rel: Relationship,
    screen_dist_px: float,
    passive_px: float,
    world_tol: float,
) -> float:
    """Return a ranking score, higher is better.

    Family priority dominates; screen proximity and residual refine it.
    """
    w_type = FAMILY_PRIORITY.get(rel.family, 0)
    w_feature = rel.base_priority
    passive = max(passive_px, 1.0)
    tol = max(world_tol, 1e-9)
    f_screen = max(0.0, 1.0 - screen_dist_px / passive)
    f_res = max(0.0, 1.0 - rel.residual / tol)
    return (
        w_type * _TYPE_WEIGHT
        + w_feature * _FEATURE_WEIGHT
        + f_screen * _SCREEN_WEIGHT
        + f_res * _RESIDUAL_WEIGHT
       - screen_dist_px
    )


def screen_score(family: str, screen_dist_px: float) -> float:
    """Return a family-priority-minus-distance score (legacy, used by tests)."""
    return FAMILY_PRIORITY.get(family, 0) * _TYPE_WEIGHT - screen_dist_px


@dataclass
class RankItem:
    """Scored relationship with screen-space metrics."""
    key: tuple  # NMS identity, e.g. (family, axis, target_entity)
    score: float
    screen_dist: float
    payload: Relationship
    screen_anchor: tuple[float, float] | None = None  # for spatial NMS


def _nms_slot(key: tuple) -> tuple:
    """Return the (family, axis) slot used for one-per-slot suppression.

    Compatible slots (different axes or families) must not suppress each other;
    only duplicates within the same slot compete.
    """
    return key[:2] if len(key) >= 2 else key


def rank(
    items: list[RankItem],
    passive_px: float,
    *,
    top_k: int = 3,
    nms_px: float = 20.0,
) -> tuple[list[RankItem], list[RankItem]]:
    """Filter, score-sort, and keep at most one guide per snap slot.

    Returns ``(kept, visible)``: the top ``top_k`` after slot suppression, and
    every item within ``passive_px``. ``nms_px`` is unused.
    """
    del nms_px  # one-per-slot suppression replaces pixel NMS
    visible = [it for it in items if it.screen_dist <= passive_px]
    visible.sort(key=lambda it: (-it.score, it.screen_dist, it.key))

    kept: list[RankItem] = []
    seen_keys: set[tuple] = set()
    used_slots: set[tuple] = set()

    for it in visible:
        if it.key in seen_keys:
            continue
        # One guide per (family, axis) slot.
        slot = _nms_slot(it.key)
        if slot in used_slots:
            continue
        used_slots.add(slot)
        seen_keys.add(it.key)
        kept.append(it)
        if len(kept) >= top_k:
            break
    return kept, visible


def with_engaged(
    ranked: list[RankItem],
    pool: list[RankItem],
    engaged_keys: set[tuple],
    top_k: int,
) -> list[RankItem]:
    """Return the guides to draw: every engaged item first, then ``ranked``.

    An engaged guide can hold its latch from outside the decluttered top-K
    (it is then only in ``pool``); it must still be drawn, or a snap applies
    with no visible guide. Ranked items sharing a slot with an engaged one are
    dropped, and the list is capped at ``top_k`` unless the engaged guides
    alone exceed it.
    """
    engaged: list[RankItem] = []
    seen: set[tuple] = set()
    for it in pool:
        if it.key in engaged_keys and it.key not in seen:
            seen.add(it.key)
            engaged.append(it)
    slots = {_nms_slot(it.key) for it in engaged}
    rest = [
        it for it in ranked if it.key not in seen and _nms_slot(it.key) not in slots
    ]
    return engaged + rest[: max(0, top_k - len(engaged))]
