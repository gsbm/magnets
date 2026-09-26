"""Alignment, guide glyphs, basic ranking, resolve, and point-index tests."""

from core.features import PointFeature, PointKind
from core.frames import WORLD_AXES
from core.guide_draw import axis_parallel_segment
from core.relationship import ConstraintDelta, GuideLine, Relationship
from core.resolver import resolve_translation
from core.scoring import RankItem, rank, screen_score
from core.solvers.alignment import AlignmentSolver
from core.solvers.base import SolveContext
from core.spatial import PointIndex
from draw.glyphs import dash_segments, extend_segment
from mathutils import Vector


def _pt(co, kind=PointKind.ORIGIN, entity="A"):
    return PointFeature.from_name(Vector(co), kind, entity)


def test_alignment_x_axis_residual_and_delta():
    # Per-axis model: the X guide fires on the X-coordinate gap and corrects
    # along X only (the Y/Z offset is left free).
    solver = AlignmentSolver()
    moving = [_pt((2.0, 3.0, 0.0), entity="move")]
    targets = [_pt((0.0, 1.0, 0.0), entity="tgt")]
    ctx = SolveContext(axes=WORLD_AXES, world_tol=5.0)

    rels = solver.solve(moving, targets, ctx)
    x_rels = [r for r in rels if r.axis == "X"]
    assert len(x_rels) == 1

    rel = x_rels[0]
    assert rel.residual == 2.0
    assert rel.delta.translation == Vector((-2.0, 0.0, 0.0))
    assert (moving[0].co + rel.delta.translation).x == targets[0].co.x


def test_alignment_skips_same_entity_and_out_of_tolerance():
    solver = AlignmentSolver()
    moving = [_pt((2.0, 3.0, 0.0), entity="obj")]
    # Same-entity target is skipped; the far target is out of tolerance on
    # every axis (X 2, Y 2, Z 5 all > 0.5), so no axis aligns.
    targets = [_pt((0.0, 1.0, 0.0), entity="obj"), _pt((0.0, 1.0, 5.0), entity="far")]
    ctx = SolveContext(axes=WORLD_AXES, world_tol=0.5)

    rels = solver.solve(moving, targets, ctx)
    assert rels == []


def test_alignment_already_satisfied_residual_zero():
    # Moving and target already share Y (and Z): those axes report residual 0
    # and a zero correction.
    solver = AlignmentSolver()
    moving = [_pt((5.0, 1.0, 0.0), entity="move")]
    targets = [_pt((0.0, 1.0, 0.0), entity="tgt")]
    ctx = SolveContext(axes=WORLD_AXES, world_tol=1.0)

    rels = [r for r in solver.solve(moving, targets, ctx) if r.axis == "Y"]
    assert len(rels) == 1
    assert rels[0].residual == 0.0
    assert rels[0].delta.translation.length == 0.0


def test_dash_segments_splits_along_length():
    a = Vector((0.0, 0.0, 0.0))
    b = Vector((1.0, 0.0, 0.0))
    segs = dash_segments(a, b, dash=0.2, gap=0.1)
    assert len(segs) >= 3
    assert segs[0][0] == a
    assert segs[-1][1].x == 1.0


def test_extend_segment_adds_margin():
    a = Vector((0.0, 0.0, 0.0))
    b = Vector((1.0, 0.0, 0.0))
    p0, p1 = extend_segment(a, b, margin=0.5)
    assert p0.x == -0.5
    assert p1.x == 1.5


def test_axis_parallel_segment_spans_anchor_to_extent():
    anchor = Vector((0.0, 1.0, 0.0))
    direction = Vector((1.0, 0.0, 0.0))
    extent = Vector((3.0, 1.0, 0.0))
    p0, p1 = axis_parallel_segment(anchor, direction, extent, margin=0.0)
    assert p0 == anchor
    assert p1 == extent


def test_screen_score_prefers_higher_family_priority():
    assert screen_score("alignment", 10.0) > screen_score("alignment", 20.0)


def test_rank_filters_by_passive_range_and_dedupes():
    items = [
        RankItem(key=("alignment", "X", "A"), score=100.0, screen_dist=10.0, payload=1),
        RankItem(key=("alignment", "X", "A"), score=90.0, screen_dist=5.0, payload=2),
        RankItem(key=("alignment", "Y", "B"), score=80.0, screen_dist=30.0, payload=3),
        RankItem(key=("alignment", "Z", "C"), score=70.0, screen_dist=60.0, payload=4),
    ]
    ranked, _visible = rank(items, passive_px=48.0)
    assert [it.payload for it in ranked] == [1, 3]


def test_resolve_translation_single_constraint():
    rel = Relationship(
        family="alignment",
        axis="X",
        label="X",
        moving=_pt((2.0, 3.0, 0.0)),
        targets=(_pt((0.0, 1.0, 0.0), entity="tgt"),),
        residual=2.0,
        delta=ConstraintDelta.from_vector(Vector((0.0, -2.0, 0.0))),
        guide=GuideLine(point=Vector((0.0, 1.0, 0.0)), direction=Vector((1.0, 0.0, 0.0))),
    )
    assert resolve_translation([rel]) == Vector((0.0, -2.0, 0.0))
    assert resolve_translation([]).length == 0.0


def test_point_index_radius_and_nearest():
    feats = [
        (_pt((0.0, 0.0, 0.0)).co, "a"),
        (_pt((1.0, 0.0, 0.0)).co, "b"),
        (_pt((10.0, 0.0, 0.0)).co, "c"),
    ]
    index = PointIndex(feats)
    assert len(index) == 3
    near = index.query_radius(Vector((0.5, 0.0, 0.0)), 1.0)
    assert set(near) == {"a", "b"}
    nearest = index.query_nearest(Vector((0.4, 0.0, 0.0)), 2)
    assert nearest[0] in {"a", "b"}
