"""Ranking and active-set tests for secondary snaps (e.g. even spacing).

Covers one guide per slot in ranking, and snap-tolerance (not
release-tolerance) gating for newly engaged secondaries.
"""

from core.features import PointFeature, PointKind
from core.graph import build_active_set
from core.relationship import ConstraintDelta, GuideSegment, Relationship
from core.scoring import RankItem, rank, relationship_score, with_engaged
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


def test_with_engaged_draws_latched_guide_outside_top_k():
    def item(key, dist):
        return RankItem(key=key, score=1.0, screen_dist=dist, payload=key)

    ranked = [item(("alignment", "X", "B", "o", "o"), 2.0),
              item(("spacing", "X", "C", "o", "o"), 5.0),
              item(("midpoint", "m", "D", "o", "o"), 6.0)]
    latched = item(("alignment", "X", "A", "o", "o"), 9.0)  # only in `visible`
    out = with_engaged(ranked, ranked + [latched], {latched.key}, top_k=2)
    assert out[0] is latched, "the engaged guide is drawn first"
    assert all(it.key[:2] != ("alignment", "X") for it in out[1:]), "one per slot"
    assert [it.key[0] for it in out] == ["alignment", "spacing"], "capped at top_k"

    many = [item(("alignment", ax, "A", "o", "o"), 1.0) for ax in "XYZ"]
    keys = {it.key for it in many}
    assert len(with_engaged([], many, keys, top_k=2)) == 3, "engaged guides are never cut"


# ── Snap choice: closest first, near-ties by like-to-like then score ─────────


def _ri(key, dist, score=1.0):
    from core.scoring import RankItem

    return RankItem(key=key, score=score, screen_dist=dist, payload=key)


def test_closest_guide_wins_over_higher_score():
    from core.scoring import closest_in_zone

    origin = _ri(("alignment", "X", "T", "origin", "bbox_corner"), 14.0, score=1000.0)
    face = _ri(("alignment", "X", "T", "bbox_face_center", "bbox_face_center"), 0.5)
    assert closest_in_zone([origin, face], 16.0) is face


def test_near_tie_prefers_like_to_like_then_score():
    from core.scoring import closest_in_zone, like_to_like

    unlike = _ri(("alignment", "X", "T", "origin", "bbox_corner"), 1.0, score=900.0)
    like = _ri(("alignment", "X", "T", "bbox_corner", "bbox_face_center"), 2.5, score=10.0)
    assert like_to_like(like.key) and not like_to_like(unlike.key)
    assert closest_in_zone([unlike, like], 16.0, tie_px=2.0) is like
    # Beyond the tie window, distance decides.
    assert closest_in_zone([unlike, like], 16.0, tie_px=1.0) is unlike


def test_nothing_in_zone_or_excluded():
    from core.scoring import closest_in_zone

    a = _ri(("alignment", "X", "T", "origin", "origin"), 20.0)
    assert closest_in_zone([a], 16.0) is None
    b = _ri(("alignment", "Y", "T", "origin", "origin"), 3.0)
    assert closest_in_zone([a, b], 16.0, exclude=(b.key,)) is None


# ── Engaged set: one guide per direction, coincident spacing may confirm ─────


def _pull_rel(family, axis, delta, cdir=None):
    from core.features import PointFeature, PointKind
    from core.relationship import ConstraintDelta, GuideLine, Relationship
    from mathutils import Vector

    p = PointFeature.from_name(Vector((0, 0, 0)), PointKind.ORIGIN, "M")
    return Relationship(
        family=family, axis=axis, label="", moving=p, targets=(p,), residual=0.0,
        delta=ConstraintDelta.from_vector(Vector(delta)),
        guide=GuideLine(point=Vector((0, 0, 0)), direction=Vector((0, 1, 0))),
        constraint_dir=Vector(cdir) if cdir else None,
    )


def test_guide_covering_an_engaged_direction_does_not_engage():
    from core.graph import adds_direction

    x = _pull_rel("alignment", "X", (0.1, 0, 0), (1, 0, 0))
    y = _pull_rel("alignment", "Y", (0, 0.2, 0), (0, 1, 0))
    # Another pull along X (other spot) and a diagonal plane in the XY span.
    assert not adds_direction(_pull_rel("coplanar", "cop_A", (0.3, 0, 0), (1, 0, 0)), [x])
    assert not adds_direction(_pull_rel("coplanar", "cop_B", (0.1, 0.1, 0), (0.7071, 0.7071, 0)), [x, y])
    # A new direction is fine.
    assert adds_direction(y, [x])
    assert adds_direction(_pull_rel("coplanar", "cop_C", (0, 0, 0.1), (0, 0, 1)), [x, y])


def test_coincident_spacing_confirms_an_engaged_alignment():
    from core.graph import adds_direction

    x = _pull_rel("alignment", "X", (0.1, 0, 0), (1, 0, 0))
    same_spot = _pull_rel("spacing", "X", (0.1, 0, 0))
    other_spot = _pull_rel("spacing", "X", (0.4, 0, 0))
    assert adds_direction(same_spot, [x])
    assert not adds_direction(other_spot, [x])


# ── Drawn guides: one per direction, coincident targets as marks ─────────────


def _drawn(rel, dist):
    from core.scoring import RankItem

    key = (rel.family, rel.axis, rel.targets[0].entity, "origin", "origin")
    return RankItem(key=key, score=1.0, screen_dist=dist, payload=rel)


def test_passive_guides_only_on_free_directions():
    from core.graph import one_guide_per_direction

    x = _drawn(_pull_rel("alignment", "X", (0.1, 0, 0), (1, 0, 0)), 3.0)
    x_other = _drawn(_pull_rel("alignment", "X2", (0.5, 0, 0), (1, 0, 0)), 20.0)
    diag = _drawn(_pull_rel("midpoint", "mid", (0.2, 0.2, 0)), 25.0)
    y = _drawn(_pull_rel("alignment", "Y", (0, 0.3, 0), (0, 1, 0)), 30.0)
    drawn = one_guide_per_direction([x], [x_other, diag, y], top_k=5)
    # X is engaged; the other X guide adds nothing; the diagonal is the closest
    # new direction; after it, Y lies in the covered XY plane.
    assert [it.payload.axis for it in drawn] == ["X", "mid"]


def test_undirected_passive_guides_are_limited_to_one():
    from core.graph import one_guide_per_direction

    a = _drawn(_pull_rel("parallel", "par_A", (0, 0, 0)), 0.0)
    b = _drawn(_pull_rel("parallel", "par_B", (0, 0, 0)), 0.0)
    assert len(one_guide_per_direction([], [a, b], top_k=5)) == 1


def test_coincident_alignment_targets_become_marks():
    from core.features import PointFeature, PointKind
    from core.graph import coincident_targets
    from core.relationship import ConstraintDelta, GuideLine, Relationship
    from mathutils import Vector

    m = PointFeature.from_name(Vector((0, 0, 0)), PointKind.ORIGIN, "M")

    def align(entity, x, y):
        t = PointFeature.from_name(Vector((x, y, 0)), PointKind.ORIGIN, entity)
        return Relationship(
            family="alignment", axis="X", label="", moving=m, targets=(t,), residual=0.0,
            delta=ConstraintDelta.from_vector(Vector((x, 0, 0))),
            guide=GuideLine(point=t.co.copy(), direction=Vector((0, 1, 0))),
            constraint_dir=Vector((1, 0, 0)),
        )

    engaged = align("A", 2.0, 5.0)
    pool = [_drawn(r, 1.0) for r in (align("B", 2.0, -3.0), align("C", 2.0, 8.0), align("D", 2.5, 1.0))]
    marks = coincident_targets(engaged, pool)
    assert sorted(round(v.y) for v in marks) == [-3, 8], "B and C line up, D does not"


def test_depth_axis_cutoff_angle():
    import math

    from core.frames import world_axes
    from core.solvers.base import SolveContext
    from core.view_filter import depth_threshold
    from mathutils import Vector

    ray = Vector((0.0, math.sin(math.radians(40)), -math.cos(math.radians(40))))  # 40° off -Z
    z = Vector((0, 0, 1))
    wide = SolveContext(axes=world_axes(), world_tol=1.0, view_normal=ray,
                        depth_threshold=depth_threshold(math.radians(45)))
    narrow = SolveContext(axes=world_axes(), world_tol=1.0, view_normal=ray,
                          depth_threshold=depth_threshold(math.radians(30)))
    assert wide.direction_hidden(z), "Z is 40° from the view: hidden by a 45° cutoff"
    assert not narrow.direction_hidden(z), "and kept by a 30° cutoff"
    assert not wide.direction_hidden(Vector((1, 0, 0)))
