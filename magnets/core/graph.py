"""Relationship compatibility and active constraint sets."""

from __future__ import annotations

from .relationship import GuideLine, Relationship
from .scoring import TIE_PX, RankItem, closest_in_zone, snap_tier

# Orthogonal translation families that generally compose with each other.
_TRANSLATION_FAMILIES = frozenset(
    {"alignment", "midpoint", "spacing", "repeat_size", "symmetry", "collinear", "coplanar"}
)


def snap_axis_slot(rel: Relationship) -> str:
    """Return the exclusivity slot for ``rel`` (one engaged guide per slot).

    Orthogonal axes (e.g. ``alignment:X`` vs ``alignment:Y``) use different
    slots and may compose.
    """
    if rel.family == "alignment":
        return f"alignment:{rel.axis}"
    return f"{rel.family}:{rel.axis}"


def constraints_compatible(a: Relationship, b: Relationship) -> bool:
    """Return True if ``a`` and ``b`` may be satisfied together."""
    if snap_axis_slot(a) == snap_axis_slot(b):
        return False
    if a.family == "alignment" and b.family == "alignment":
        return a.axis != b.axis
    if a.family == b.family and a.axis == b.axis:
        return False
    if a.family in _TRANSLATION_FAMILIES and b.family in _TRANSLATION_FAMILIES:
        return True
    return a.family == b.family


def _pull_direction(rel: Relationship):
    """Unit direction a relationship constrains, or None (no translation)."""
    if rel.constraint_dir is not None and rel.constraint_dir.length > 1e-9:
        return rel.constraint_dir.normalized()
    t = rel.delta.translation
    return t.normalized() if t.length > 1e-9 else None


def competes(a: Relationship, b: Relationship) -> bool:
    """True when ``a`` and ``b`` pull along the same direction.

    Only one of them can hold that direction; the other is redundant (same
    spot) or contradicting (another spot), so it must not engage as well.
    Exception: equal spacing landing on the very spot another guide holds
    ("aligned *and* evenly spaced") confirms it, so it may engage too.
    """
    da, db = _pull_direction(a), _pull_direction(b)
    if da is None or db is None:
        return False
    if abs(da.dot(db)) <= 0.9:
        return False
    if "spacing" in (a.family, b.family):
        pa = a.delta.translation.dot(da)
        pb = b.delta.translation.dot(da)
        if abs(pa - pb) <= 1e-4 * (1.0 + abs(pa)):
            return False
    return True


# |cos| between a guide's pull and the drag below which the guide is idle.
_IDLE_COS = 0.2
# |cos| between a guide line and the drag above which the drag runs along it.
_ALONG_COS = (1.0 - _IDLE_COS**2) ** 0.5


def drop_idle_satisfied(
    items: list[RankItem],
    motion,
    *,
    satisfied: float,
    snap_px: float,
) -> list[RankItem]:
    """Drop guides already met across the drag, and those that would undo them.

    Sliding along X on a row that is already Y-aligned, the Y alignment has no
    correction to give and only crowds out the X guides (equal spacing). A
    guide within ``satisfied`` (world) that the drag keeps met is dropped:
    its pull is (nearly) perpendicular to ``motion``, or, with no pull, it is
    a line the drag runs along (edge on edge). What it holds stays held: other
    guides pulling along a held direction would only drag the selection off
    its row, so they go too. Alignments stay while an alignment along the
    drag is in the snap zone, so the corner where the two lines cross still
    shows. ``motion`` None (no drag yet) keeps all.
    """
    if motion is None or motion.length <= 1e-9:
        return items
    m = motion.normalized()

    def stays_met(rel: Relationship):
        """The direction ``rel`` holds as ("pull"|"line", vec), or None."""
        if rel.residual > satisfied:
            return None
        d = _pull_direction(rel)
        if d is not None:
            return ("pull", d) if abs(d.dot(m)) <= _IDLE_COS else None
        if isinstance(rel.guide, GuideLine) and rel.guide.direction.length > 1e-9:
            line = rel.guide.direction.normalized()
            return ("line", line) if abs(line.dot(m)) >= _ALONG_COS else None
        return None

    def undoes(d, held) -> bool:
        kind, v = held
        if kind == "pull":
            return abs(d.dot(v)) > 0.9
        return abs(d.dot(v)) <= _IDLE_COS  # pulls off the held line

    crossing = any(
        it.payload.family == "alignment"
        and it.screen_dist <= snap_px
        and (d := _pull_direction(it.payload)) is not None
        and abs(d.dot(m)) > _IDLE_COS
        for it in items
    )
    met = {id(it): stays_met(it.payload) for it in items}
    held = [h for h in met.values() if h is not None]
    out = []
    for it in items:
        if met[id(it)] is not None:
            if crossing and it.payload.family == "alignment":
                out.append(it)
            continue
        d = _pull_direction(it.payload)
        if d is not None and any(undoes(d, h) for h in held):
            continue
        out.append(it)
    return out


def adds_direction(rel: Relationship, selected: list[Relationship]) -> bool:
    """True when ``rel`` constrains a direction ``selected`` does not cover.

    A guide pulling mostly within the span of the engaged ones is redundant
    or contradicting; coincident equal spacing is the exception (see
    ``competes``). Guides without a translation always pass.
    """
    d = _pull_direction(rel)
    if d is None:
        return True
    residual = d.copy()
    for b in _basis_of(selected):
        residual -= b * residual.dot(b)
    if residual.length > 0.45:
        return True
    # Covered: only coincident spacing (confirming a held spot) may join. For
    # parallel pulls ``competes`` is False exactly in that case.
    for existing in selected:
        e = _pull_direction(existing)
        if e is not None and abs(e.dot(d)) > 0.9 and not competes(rel, existing):
            return True
    return False


def _basis_of(selected: list[Relationship]) -> list:
    """Orthonormal basis of the directions ``selected`` constrain."""
    basis: list = []
    for rel in selected:
        v = _pull_direction(rel)
        if v is None:
            continue
        v = v.copy()
        for b in basis:
            v -= b * v.dot(b)
        if v.length > 1e-6:
            basis.append(v.normalized())
    return basis


def build_active_set(
    primary: RankItem,
    ranked: list[RankItem],
    *,
    snap_px: float,
    release_px: float | None = None,
    max_constraints: int = 3,
    visible: list[RankItem] | None = None,
    sticky_keys: set[tuple] | None = None,
    tie_px: float = TIE_PX,
) -> list[Relationship]:
    """Build the engaged constraint set, including ``primary``, from ``ranked``.

    New secondaries engage within ``snap_px``, picked one at a time from
    everything in range with the primary's rule (``closest_in_zone``: closest,
    then like-to-like, then score). Guides in ``sticky_keys`` (already latched)
    hold within ``release_px`` and may re-attach from ``visible``.
    """
    hold_px = release_px if release_px is not None else snap_px
    selected: list[Relationship] = [primary.payload]
    used_keys: set[tuple] = {primary.key}
    used_slots: set[str] = {snap_axis_slot(primary.payload)}

    def can_add(item: RankItem, max_dist: float) -> bool:
        if item.key in used_keys:
            return False
        if snap_tier(item.key) > 0:
            return False  # niche guides snap alone, never stacked
        if item.screen_dist > max_dist:
            return False
        if len(selected) >= max_constraints:
            return False
        if snap_axis_slot(item.payload) in used_slots:
            return False
        if not all(constraints_compatible(item.payload, existing) for existing in selected):
            return False
        return adds_direction(item.payload, selected)

    def add(item: RankItem) -> None:
        selected.append(item.payload)
        used_keys.add(item.key)
        used_slots.add(snap_axis_slot(item.payload))

    def try_add(item: RankItem, max_dist: float) -> bool:
        if not can_add(item, max_dist):
            return False
        add(item)
        return True

    # New secondaries use snap_px; release_px is only for already-latched holds.
    pool = [
        it for it in (visible if visible is not None else ranked)
        if it.screen_dist <= snap_px and snap_tier(it.key) == 0
    ]
    while len(selected) < max_constraints:
        pick = closest_in_zone(
            [it for it in pool if can_add(it, snap_px)], snap_px, tie_px=tie_px
        )
        if pick is None:
            break
        add(pick)

    if sticky_keys and visible:
        for item in visible:
            if item.key not in sticky_keys:
                continue
            try_add(item, hold_px)

    return selected


def one_guide_per_direction(
    engaged: list[RankItem],
    pool: list[RankItem],
    top_k: int,
) -> list[RankItem]:
    """The guides to draw: every engaged one, then passive ones by direction.

    A passive guide is drawn only if it adds an uncovered direction
    (``adds_direction``), closest first, primary tier before secondary. At
    most one passive guide without a direction is kept. Capped at ``top_k``
    unless the engaged guides alone exceed it.
    """
    kept = list(engaged)
    rels = [it.payload for it in kept]
    keys = {it.key for it in kept}
    slots = {snap_axis_slot(it.payload) for it in kept}
    undirected = 0
    for it in sorted(pool, key=lambda it: (snap_tier(it.key), it.screen_dist)):
        if len(kept) >= top_k:
            break
        if it.key in keys or snap_axis_slot(it.payload) in slots:
            continue
        if _pull_direction(it.payload) is None:
            if undirected:
                continue
            undirected += 1
        elif not adds_direction(it.payload, rels):
            continue
        kept.append(it)
        rels.append(it.payload)
        keys.add(it.key)
        slots.add(snap_axis_slot(it.payload))
    return kept


def coincident_targets(
    rel: Relationship,
    pool: list[RankItem],
    limit: int = 8,
) -> list:
    """Anchors of other objects' alignment targets on ``rel``'s coordinate.

    For an engaged alignment: every other object whose aligned feature sits
    on the same coordinate of the same axis ("these line up"), so one line
    plus a mark per object replaces a line per object.
    """
    if rel.family != "alignment" or rel.constraint_dir is None:
        return []
    d = rel.constraint_dir.normalized()
    own = rel.targets[0]
    coord = own.co.dot(d) if hasattr(own, "co") else None
    if coord is None:
        return []
    eps = 1e-5 * (1.0 + abs(coord))
    seen = {own.entity}
    out = []
    for it in pool:
        other = it.payload
        if other.family != "alignment" or other.axis != rel.axis:
            continue
        target = other.targets[0]
        if target.entity in seen or not hasattr(target, "co"):
            continue
        if abs(target.co.dot(d) - coord) <= eps:
            seen.add(target.entity)
            out.append(target.co.copy())
            if len(out) >= limit:
                break
    return out
