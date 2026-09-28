"""Constraint-family solver smoke tests (midpoint, spacing, size, etc.)."""

import core.solvers  # noqa: F401
from core import families as family_ids
from core.bbox import bbox_dimensions, bbox_edges, bbox_face_planes
from core.features import (
    BBoxFeature,
    CircleFeature,
    EntityRef,
    FeaturePool,
    LineFeature,
    PlaneFeature,
    PointFeature,
    PointKind,
)
from core.frames import world_axes
from core.guide_draw import circle_segments, guide_to_drawables
from core.registry import dispatch
from core.relationship import GuideCircle, GuidePlane, GuideSegment
from core.solvers.base import SolveContext
from core.solvers.collinear import CollinearSolver
from core.solvers.concentric import ConcentricSolver
from core.solvers.coplanar import CoplanarSolver
from core.solvers.equal_size import EqualSizeSolver
from core.solvers.midpoint import MidpointSolver
from core.solvers.parallel import ParallelSolver
from core.solvers.spacing import SpacingSolver
from core.solvers.symmetry import SymmetrySolver
from core.solvers.tangency import TangencySolver
from core.transform import TransformMode
from mathutils import Vector


def _pt(co, kind=PointKind.ORIGIN, entity="A"):
    return PointFeature.from_name(Vector(co), kind, entity)


def _ctx(tol=1.0):
    return SolveContext(axes=world_axes(), world_tol=tol, unit_scale=1.0)


def test_midpoint_solver_finds_center():
    solver = MidpointSolver()
    moving = [_pt((2.0, 2.0, 0.0), entity="move")]
    targets = [_pt((0.0, 0.0, 0.0), entity="t"), _pt((4.0, 4.0, 0.0), entity="t")]
    rels = solver.solve(moving, targets, _ctx(5.0))
    assert rels
    assert rels[0].residual == 0.0


def test_midpoint_solver_pairs_only_same_kind_features():
    """Origin + face center has no geometric midpoint; corner + corner does."""
    solver = MidpointSolver()
    moving = [_pt((1.0, 0.0, 0.0), entity="move")]
    mixed = [
        _pt((0.0, 0.0, 0.0), PointKind.ORIGIN, "t"),
        _pt((2.0, 0.0, 0.0), PointKind.BBOX_FACE_CENTER, "t"),
    ]
    assert solver.solve(moving, mixed, _ctx(5.0)) == []
    corners = [
        _pt((0.0, 0.0, 0.0), PointKind.BBOX_CORNER, "t"),
        _pt((2.0, 0.0, 0.0), PointKind.BBOX_CORNER, "t"),
    ]
    rels = solver.solve(moving, corners, _ctx(5.0))
    assert len(rels) == 1 and rels[0].residual == 0.0


def test_spacing_solver_detects_equal_gap():
    solver = SpacingSolver()
    moving = [_pt((4.0, 0.0, 0.0), entity="move")]
    targets = [_pt((0.0, 0.0, 0.0), entity="t"), _pt((2.0, 0.0, 0.0), entity="t")]
    rels = solver.solve(moving, targets, _ctx(0.5))
    assert rels


def test_equal_size_solver_matches_bbox_width():
    solver = EqualSizeSolver()
    ref = EntityRef(name="a")
    moving = [BBoxFeature(Vector((0, 0, 0)), Vector((2.0, 1.0, 1.0)), ref)]
    target = [BBoxFeature(Vector((5, 0, 0)), Vector((2.0, 3.0, 1.0)), EntityRef(name="b"))]
    ctx = _ctx(2.0)
    ctx.transform_mode = TransformMode.SCALE
    rels = solver.solve(moving, target, ctx)
    assert any(r.axis.startswith("size_") for r in rels)


def test_equal_size_solver_is_scale_only():
    """A move/rotate cannot change size; a same-size neighbour must not engage
    (it would claim the X/Y/Z snap slot at 0 px and block real alignments)."""
    solver = EqualSizeSolver()
    moving = [BBoxFeature(Vector((0, 0, 0)), Vector((2.0, 2.0, 2.0)), EntityRef(name="a"))]
    target = [BBoxFeature(Vector((5, 0, 0)), Vector((2.0, 2.0, 2.0)), EntityRef(name="b"))]
    for mode in (TransformMode.TRANSLATE, TransformMode.ROTATE):
        ctx = _ctx(2.0)
        ctx.transform_mode = mode
        assert solver.solve(moving, target, ctx) == []


def test_collinear_point_to_line():
    solver = CollinearSolver()
    moving = [_pt((1.0, 1.0, 0.0), entity="move")]
    line = LineFeature(Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), "edge", EntityRef("t"))
    rels = solver.solve(moving, [line], _ctx(1.0))
    assert rels
    assert rels[0].residual <= 1.0


def test_coplanar_point_to_plane():
    solver = CoplanarSolver()
    moving = [_pt((0.0, 0.0, 1.0), entity="move")]
    plane = PlaneFeature(Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), "face", EntityRef("t"))
    rels = solver.solve(moving, [plane], _ctx(1.0))
    assert rels
    assert rels[0].residual == 1.0


def test_parallel_lines():
    solver = ParallelSolver()
    a = LineFeature(Vector((0, 0, 0)), Vector((1, 0, 0)), "a", EntityRef("a"))
    b = LineFeature(Vector((0, 1, 0)), Vector((1, 0, 0)), "b", EntityRef("b"))
    rels = solver.solve([a], [b], _ctx(2.0))
    assert rels


def test_concentric_circles():
    solver = ConcentricSolver()
    m = CircleFeature(Vector((1, 0, 0)), Vector((0, 0, 1)), 1.0, "c", EntityRef("m"))
    c = CircleFeature(Vector((0, 0, 0)), Vector((0, 0, 1)), 2.0, "c", EntityRef("t"))
    rels = solver.solve([m], [c], _ctx(2.0))
    assert rels


def test_tangency_external_circles():
    solver = TangencySolver()
    m = CircleFeature(Vector((3.5, 0, 0)), Vector((0, 0, 1)), 1.0, "c", EntityRef("m"))
    c = CircleFeature(Vector((0, 0, 0)), Vector((0, 0, 1)), 2.0, "c", EntityRef("t"))
    rels = solver.solve([m], [c], _ctx(0.5))
    assert rels


def test_symmetry_solver_reflects_across_plane():
    solver = SymmetrySolver()
    moving = [_pt((1.0, 2.0, 3.0), entity="move")]
    target = [_pt((1.0, -2.0, 3.0), entity="t")]
    rels = solver.solve(moving, target, _ctx(0.5))
    assert rels


def test_dispatch_runs_multiple_families():
    moving = FeaturePool(
        points=[_pt((2.0, 3.0, 0.0), entity="move")],
        bboxes=[BBoxFeature(Vector((0, 0, 0)), Vector((2, 2, 2)), EntityRef("move"))],
    )
    candidates = FeaturePool(
        points=[_pt((0.0, 1.0, 0.0), entity="tgt"), _pt((0.0, 3.0, 0.0), entity="tgt")],
        bboxes=[BBoxFeature(Vector((5, 0, 0)), Vector((2, 2, 2)), EntityRef("tgt"))],
    )
    rels = dispatch(moving, candidates, _ctx(5.0), set(family_ids.FAMILY_IDS))
    found = {r.family for r in rels}
    assert "alignment" in found


def test_bbox_helpers():
    corners = [Vector(c) for c in (
        (-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1),
        (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1),
    )]
    assert len(bbox_edges(corners)) == 12
    assert len(bbox_face_planes(corners)) == 6
    assert bbox_dimensions(corners) == Vector((2.0, 2.0, 2.0))


def test_guide_to_drawables_variants():
    assert guide_to_drawables(GuideSegment(Vector((0, 0, 0)), Vector((1, 0, 0))), Vector((0, 0, 0)))
    assert guide_to_drawables(
        GuideCircle(Vector((0, 0, 0)), Vector((0, 0, 1)), 1.0), Vector((0, 0, 0))
    )
    assert guide_to_drawables(
        GuidePlane(Vector((0, 0, 0)), Vector((0, 0, 1))), Vector((0, 0, 0))
    )
    segs = circle_segments(Vector((0, 0, 0)), Vector((0, 0, 1)), 1.0, segments=8)
    assert len(segs) == 8
