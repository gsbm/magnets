"""Distribution / even-spacing solver unit tests (bpy-free core)."""

import core.solvers  # noqa: F401 - register solver table
from core.features import PointFeature, PointKind
from core.frames import world_axes
from core.guide_draw import (
    dedupe_segments,
    equal_span_marks,
    guide_to_drawables,
    segment_key,
)
from core.relationship import GuideSpans
from core.solvers.base import SolveContext
from core.solvers.distribution import DistributionSolver
from mathutils import Vector


def _pt(co, kind=PointKind.ORIGIN, entity="A"):
    return PointFeature.from_name(Vector(co), kind, entity)


def _ctx(tol=0.5, metric="both"):
    return SolveContext(
        axes=world_axes(), world_tol=tol, unit_scale=1.0, spacing_metric=metric
    )


def _best_toward(rels, axis="X"):
    """The lowest-residual relationship on the given axis, or None."""
    on_axis = [r for r in rels if r.axis == axis]
    return min(on_axis, key=lambda r: r.residual) if on_axis else None


def test_rhythm_extends_row_by_matching_gap():
    # A at x=0, B at x=2 → gap 2. Dragged object near x=4 should snap to x=4,
    # continuing the rhythm to the right of B.
    solver = DistributionSolver()
    cand = [_pt((0.0, 0.0, 0.0), entity="a"), _pt((2.0, 0.0, 0.0), entity="b")]
    moving = [_pt((4.1, 0.0, 0.0), entity="m")]
    rel = _best_toward(solver.solve(moving, cand, _ctx(0.5, "center")))
    assert rel is not None
    assert abs(rel.residual - 0.1) < 1e-6
    # delta slides -0.1 on X, landing the origin exactly on x=4.
    assert abs(rel.delta.translation.x + 0.1) < 1e-6
    assert abs(rel.delta.translation.y) < 1e-9


def test_gap_narrower_than_the_passive_range_still_counts():
    # Zoomed out, the passive range (world_tol) spans more than the gap
    # itself; the gap must still be measured.
    solver = DistributionSolver()
    cand = [_pt((0.0, 0.0, 0.0), entity="a"), _pt((2.0, 0.0, 0.0), entity="b")]
    moving = [_pt((4.3, 0.0, 0.0), entity="m")]
    rel = _best_toward(solver.solve(moving, cand, _ctx(3.0, "center")))
    assert rel is not None
    assert abs(rel.delta.translation.x + 0.3) < 1e-6


def test_equalize_between_two_objects_snaps_to_midpoint():
    solver = DistributionSolver()
    cand = [_pt((0.0, 0.0, 0.0), entity="a"), _pt((4.0, 0.0, 0.0), entity="b")]
    moving = [_pt((2.1, 0.0, 0.0), entity="m")]
    rel = _best_toward(solver.solve(moving, cand, _ctx(0.5, "center")))
    assert rel is not None
    assert abs(rel.delta.translation.x + 0.1) < 1e-6  # 2.1 → 2.0 (midpoint)


def _sized(center_x, half, entity):
    """Origin at the centre plus two bbox face centres at ±half on X."""
    return [
        _pt((center_x, 0.0, 0.0), PointKind.ORIGIN, entity),
        _pt((center_x - half, 0.0, 0.0), PointKind.BBOX_FACE_CENTER, entity),
        _pt((center_x + half, 0.0, 0.0), PointKind.BBOX_FACE_CENTER, entity),
    ]


def test_edge_metric_matches_visible_gap_not_centres():
    # Different-sized objects: the *edge* gaps are even but the *centre* gaps are
    # not, so "edge" fires where "center" cannot - proving the metric switch.
    # A: width 2 @ x=0  → edges [-1, 1]
    # B: width 0.5 @ x=3 → edges [2.75, 3.25];  visible gap A→B = 1.75
    solver = DistributionSolver()
    cand = _sized(0.0, 1.0, "a") + _sized(3.0, 0.25, "b")
    # Moving (width 0.5) near where its near edge continues the 1.75 gap past B:
    # near edge = 3.25 + 1.75 = 5.0 → centre 5.25. Placed at 5.3 (residual 0.05).
    moving = _sized(5.3, 0.25, "m")

    rel_edge = _best_toward(solver.solve(moving, cand, _ctx(0.5, "edge")))
    assert rel_edge is not None
    assert abs(rel_edge.residual - 0.05) < 1e-6
    assert abs(rel_edge.delta.translation.x + 0.05) < 1e-6  # 5.3 → 5.25

    # Centre gaps here are 3.0; the nearest centre target (6.0) is out of tol.
    assert solver.solve(moving, cand, _ctx(0.5, "center")) == []


def test_off_row_neighbour_is_ignored():
    # B sits off the X row (large Y offset) → fewer than two row neighbours.
    solver = DistributionSolver()
    cand = [_pt((0.0, 0.0, 0.0), entity="a"), _pt((2.0, 9.0, 0.0), entity="b")]
    moving = [_pt((4.0, 0.0, 0.0), entity="m")]
    assert solver.solve(moving, cand, _ctx(0.5, "center")) == []


def test_metric_none_emits_nothing():
    solver = DistributionSolver()
    cand = [_pt((0.0, 0.0, 0.0), entity="a"), _pt((2.0, 0.0, 0.0), entity="b")]
    moving = [_pt((4.0, 0.0, 0.0), entity="m")]
    assert solver.solve(moving, cand, _ctx(0.5, "off")) == []


def test_guide_marks_two_equal_gaps_on_the_row():
    # Rhythm right of B: the guide should carry the new gap and the reference
    # gap, both the same length, on the row line (y=z=0).
    solver = DistributionSolver()
    cand = [_pt((0.0, 0.0, 0.0), entity="a"), _pt((2.0, 0.0, 0.0), entity="b")]
    moving = [_pt((4.05, 0.0, 0.0), entity="m")]
    rel = _best_toward(solver.solve(moving, cand, _ctx(0.5, "center")))
    guide = rel.guide
    assert isinstance(guide, GuideSpans)
    assert len(guide.gaps) == 2
    lengths = sorted((b - a).length for a, b in guide.gaps)
    assert abs(lengths[0] - lengths[1]) < 1e-6  # the two gaps are equal
    assert all(abs(p.y) < 1e-9 and abs(p.z) < 1e-9 for a, b in guide.gaps for p in (a, b))


def test_equal_span_marks_render_bar_caps_and_badge():
    segs = equal_span_marks(Vector((0, 0, 0)), Vector((2, 0, 0)), Vector((1, 0, 0)))
    # bar + 2 end caps + 2 hash strokes
    assert len(segs) == 5
    assert segs[0] == (Vector((0, 0, 0)), Vector((2, 0, 0)))  # the measured bar
    # caps/badges are perpendicular to the axis (no X component along the stroke)
    for a, b in segs[1:]:
        assert abs((b - a).x) < 1e-9
    # a GuideSpans with N gaps expands to 5*N segments, minus the end caps that
    # adjacent equal gaps share (drawn once)
    spans = GuideSpans(
        gaps=((Vector((0, 0, 0)), Vector((2, 0, 0))), (Vector((2, 0, 0)), Vector((4, 0, 0)))),
        axis=Vector((1, 0, 0)),
    )
    assert len(guide_to_drawables(spans, Vector((0, 0, 0)))) == 9


def test_dedupe_segments_drops_identical_strokes_either_way():
    a, b, c = Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0))
    assert segment_key(a, b) == segment_key(b, a)
    assert segment_key(a, b) != segment_key(a, c)
    segs = [(a, b), (b, a), (a, c), (a + Vector((1e-9, 0, 0)), b)]
    assert dedupe_segments(segs) == [(a, b), (a, c)]
    # A coarser tolerance merges near-identical strokes too.
    near = [(a, b), (a, b + Vector((0.004, 0, 0)))]
    assert len(dedupe_segments(near, eps=0.01)) == 1
    assert len(dedupe_segments(near)) == 2
