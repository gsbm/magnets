"""Ranking and active-set tests for secondary snaps (e.g. even spacing).

Covers one guide per slot in ranking, and snap-tolerance (not
release-tolerance) gating for newly engaged secondaries.
"""

from core.features import PointFeature, PointKind
from core.graph import build_active_set
from core.relationship import ConstraintDelta, GuideSegment, Relationship
from core.scoring import RankItem, rank, relationship_score
from mathutils import Vector


def _rel(family, axis, dx, entity="tgt"):
    m = PointFeature.from_name(Vector((0.0, 0.0, 0.0)), PointKind.ORIGIN, "move")
    t = PointFeature.from_name(Vector((dx, 0.0, 0.0)), PointKind.ORIGIN, entity)
    return Relationship(
        family=family,
        axis=axis,
        label="",
        moving=m,
        targets=(t,),
        residual=abs(dx),
        delta=ConstraintDelta.from_vector(Vector((dx, 0.0, 0.0))),
        guide=GuideSegment(a=m.co.copy(), b=t.co.copy()),
    )


def _item(rel, screen_dist, anchor=(0.0, 0.0)):
    return RankItem(
        key=(rel.family, rel.axis, rel.target_entity),
        score=relationship_score(rel, screen_dist, 48.0, 1.0),
        screen_dist=screen_dist,
        payload=rel,
        screen_anchor=anchor,
    )


def test_rank_keeps_one_guide_per_slot():
    # Two alignment:X guides to different neighbours, far apart on screen. Only
    # one may ever apply, so ranking must keep a single one - not let both eat
    # display slots that a different family's actionable snap needs.
    items = [
        _item(_rel("alignment", "X", 0.05, "A"), 5.0, (0.0, 0.0)),
        _item(_rel("alignment", "X", 0.06, "B"), 6.0, (500.0, 500.0)),
        _item(_rel("spacing", "X", 0.10, "row"), 8.0, (10.0, 10.0)),
    ]
    ranked, _ = rank(items, passive_px=48.0, top_k=5, nms_px=20.0)
    slots = [(it.payload.family, it.payload.axis) for it in ranked]
    assert slots.count(("alignment", "X")) == 1
    assert ("spacing", "X") in slots  # the secondary snap survives


def test_new_secondary_must_be_within_snap_not_release():
    # A far alignment:X (50px, inside release 56 but outside snap 16) must NOT be
    # glued as a fresh secondary - otherwise it hijacks the primary snap.
    primary = _item(_rel("alignment", "Y", 0.0), 0.0)
    far = _item(_rel("alignment", "X", 1.0), 50.0)
    active = build_active_set(
        primary, [primary, far], snap_px=16.0, release_px=56.0, max_constraints=5
    )
    assert {r.axis for r in active} == {"Y"}


def test_sticky_secondary_is_held_within_release():
    # A previously latched guide is still held out to release_px (hysteresis).
    primary = _item(_rel("alignment", "Y", 0.0), 0.0)
    sticky = _item(_rel("alignment", "X", 1.0, "S"), 50.0)
    active = build_active_set(
        primary,
        [primary],
        snap_px=16.0,
        release_px=56.0,
        max_constraints=5,
        visible=[primary, sticky],
        sticky_keys={sticky.key},
    )
    assert {r.axis for r in active} == {"X", "Y"}
