"""Guides already met across the drag are dropped (``drop_idle_satisfied``)."""

from core.features import PointFeature, PointKind
from core.graph import drop_idle_satisfied
from core.relationship import ConstraintDelta, GuideLine, GuideSegment, Relationship
from core.scoring import RankItem
from mathutils import Vector

X, Y = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))


def _rel(family, axis, pull, gap, entity="tgt", guide=None):
    m = PointFeature.from_name(Vector(), PointKind.ORIGIN, "move")
    t = PointFeature.from_name(pull * gap if pull else Vector(), PointKind.ORIGIN, entity)
    return Relationship(
        family=family,
        axis=axis,
        label="",
        moving=m,
        targets=(t,),
        residual=abs(gap),
        delta=ConstraintDelta.from_vector(pull * gap if pull else Vector()),
        guide=guide or GuideSegment(a=m.co.copy(), b=t.co.copy()),
        constraint_dir=pull.copy() if pull else None,
    )


def _item(rel, screen_dist):
    return RankItem(key=(rel.family, rel.axis, rel.target_entity), score=0.0,
                    screen_dist=screen_dist, payload=rel)


def _kept(items, motion):
    out = drop_idle_satisfied(items, motion, satisfied=1e-4, snap_px=16.0)
    return [(it.payload.family, it.payload.axis, it.payload.target_entity) for it in out]


def test_met_alignment_across_the_drag_gives_way_to_spacing():
    items = [
        _item(_rel("alignment", "Y", Y, 0.0, "A"), 0.0),
        _item(_rel("spacing", "X", X, 0.3, "row"), 12.0),
    ]
    assert _kept(items, X) == [("spacing", "X", "row")]


def test_other_guides_may_not_pull_off_a_held_row():
    # The row is held on Y: a Y alignment to another feature would drag the
    # selection off it, so it goes too.
    items = [
        _item(_rel("alignment", "Y", Y, 0.0, "A"), 0.0),
        _item(_rel("alignment", "Y", Y, 0.5, "B"), 10.0),
        _item(_rel("spacing", "X", X, 0.3, "row"), 12.0),
    ]
    assert _kept(items, X) == [("spacing", "X", "row")]


def test_near_miss_across_the_drag_still_snaps():
    # Not met yet: a straight X drag must still pull Y onto the alignment.
    items = [
        _item(_rel("alignment", "Y", Y, 0.03, "A"), 2.0),
        _item(_rel("alignment", "X", X, 0.02, "A"), 1.0),
    ]
    assert len(_kept(items, X)) == 2


def test_met_alignment_stays_for_a_corner():
    # An X alignment in the snap zone: the met Y line marks the corner.
    items = [
        _item(_rel("alignment", "Y", Y, 0.0, "A"), 0.0),
        _item(_rel("alignment", "X", X, 0.02, "B"), 5.0),
    ]
    assert len(_kept(items, X)) == 2


def test_met_alignment_along_a_diagonal_drag_stays():
    items = [_item(_rel("alignment", "Y", Y, 0.0, "A"), 0.0)]
    assert len(_kept(items, Vector((1.0, 1.0, 0.0)))) == 1


def test_edge_on_edge_along_the_drag_is_dropped():
    line = GuideLine(point=Vector(), direction=X.copy())
    items = [
        _item(_rel("parallel", "par_A", None, 0.0, "A", guide=line), 0.0),
        _item(_rel("spacing", "X", X, 0.3, "row"), 12.0),
    ]
    assert _kept(items, X) == [("spacing", "X", "row")]
    # Dragging across the edge, it is not held any more: kept.
    assert len(_kept(items, Y)) == 2


def test_no_drag_keeps_everything():
    items = [_item(_rel("alignment", "Y", Y, 0.0, "A"), 0.0)]
    assert len(_kept(items, None)) == 1
