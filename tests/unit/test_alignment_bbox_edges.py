"""BBox features, alignment labels, and edge-alignment solver tests."""

from core.bbox import bbox_centroid, bbox_face_centers
from core.features import EntityRef, LineFeature, PointFeature, PointKind
from core.frames import world_axes
from core.labels import alignment_label, feature_hint, point_kind_label
from core.solvers.alignment import AlignmentSolver, EdgeAlignmentSolver
from core.solvers.base import SolveContext
from draw.glyphs import endpoint_ticks, guide_ticks
from mathutils import Vector


def _corners():
    return [
        Vector((-1.0, -1.0, -1.0)),
        Vector((-1.0, -1.0, 1.0)),
        Vector((-1.0, 1.0, -1.0)),
        Vector((-1.0, 1.0, 1.0)),
        Vector((1.0, -1.0, -1.0)),
        Vector((1.0, -1.0, 1.0)),
        Vector((1.0, 1.0, -1.0)),
        Vector((1.0, 1.0, 1.0)),
    ]


def test_bbox_face_centers_returns_six_points():
    faces = bbox_face_centers(_corners())
    assert len(faces) == 6
    assert faces[0].x == -1.0
    assert faces[1].x == 1.0


def test_bbox_centroid_is_origin_for_symmetric_box():
    c = bbox_centroid(_corners())
    assert c is not None
    assert c.length < 1e-6


def test_alignment_label_with_distance():
    assert alignment_label("X", PointKind.ORIGIN, 2.0, 1.0) == "X · 2.000"
    assert alignment_label("Y", PointKind.CENTROID, 0.0, 1.0) == "Y"


def test_feature_hint_labels():
    assert point_kind_label(PointKind.BBOX_FACE_CENTER) == "face"
    assert feature_hint(PointFeature.from_name(Vector((0, 0, 0)), PointKind.CENTROID, "a")) == "center"


def test_alignment_aligns_bbox_corners_and_face_centers():
    """BBox face centers and corners participate in per-axis alignment."""
    solver = AlignmentSolver()
    ctx = SolveContext(axes=world_axes(), world_tol=5.0, unit_scale=1.0)

    moving = [
        PointFeature.from_name(Vector((3.0, 2.0, 0.0)), PointKind.BBOX_FACE_CENTER, "move"),
        PointFeature.from_name(Vector((4.0, 4.0, 4.0)), PointKind.BBOX_CORNER, "move"),
    ]
    targets = [
        PointFeature.from_name(Vector((3.0, 9.0, 0.0)), PointKind.BBOX_FACE_CENTER, "tgt"),
        PointFeature.from_name(Vector((4.0, 9.0, 9.0)), PointKind.BBOX_CORNER, "tgt"),
    ]
    rels = solver.solve(moving, targets, ctx)
    x_aligned = [r for r in rels if r.axis == "X"]
    kinds = {(r.moving.kind, r.target.kind) for r in x_aligned}
    assert (PointKind.BBOX_FACE_CENTER, PointKind.BBOX_FACE_CENTER) in kinds
    assert (PointKind.BBOX_CORNER, PointKind.BBOX_CORNER) in kinds
    face_rel = next(
        r for r in x_aligned if r.moving.kind == PointKind.BBOX_FACE_CENTER
    )
    assert face_rel.residual < 1e-9


def test_alignment_solver_uses_centroid_target():
    solver = AlignmentSolver()
    moving = [PointFeature.from_name(Vector((2.0, 3.0, 0.0)), PointKind.ORIGIN, "move")]
    targets = [
        PointFeature.from_name(Vector((0.0, 1.0, 0.0)), PointKind.CENTROID, "tgt")
    ]
    ctx = SolveContext(axes=world_axes(), world_tol=5.0, unit_scale=1.0)
    rels = [r for r in solver.solve(moving, targets, ctx) if r.axis == "X"]
    assert len(rels) == 1
    assert "2.000" in rels[0].label
    assert rels[0].target.kind == PointKind.CENTROID


def test_edge_alignment_requires_parallel_and_single_axis_match():
    """Parallel edges align on a shared axis; non-parallel edges do not."""
    solver = EdgeAlignmentSolver()
    ctx = SolveContext(axes=world_axes(), world_tol=0.2, unit_scale=1.0)

    moving_edge = LineFeature(
        point=Vector((3.0, 0.0, -1.0)),
        direction=Vector((0.0, 0.0, 1.0)),
        kind="bbox_edge",
        entity_ref=EntityRef(name="move"),
    )
    target_edge = LineFeature(
        point=Vector((3.0, 5.0, 2.0)),
        direction=Vector((0.0, 0.0, 1.0)),
        kind="bbox_edge",
        entity_ref=EntityRef(name="tgt"),
    )
    rels = solver.solve([moving_edge], [target_edge], ctx)
    assert {r.axis for r in rels} == {"X"}
    assert rels[0].residual < 1e-9

    skew_edge = LineFeature(
        point=Vector((3.0, 5.0, 2.0)),
        direction=Vector((0.0, 1.0, 0.0)),
        kind="bbox_edge",
        entity_ref=EntityRef(name="skew"),
    )
    assert solver.solve([moving_edge], [skew_edge], ctx) == []


def test_edge_alignment_zero_gap_touch():
    """Edge residual equals the remaining gap along the alignment axis."""
    solver = EdgeAlignmentSolver()
    ctx = SolveContext(axes=world_axes(), world_tol=0.5, unit_scale=1.0)

    moving_edge = LineFeature(
        point=Vector((1.9, -1.0, -1.0)),
        direction=Vector((0.0, 0.0, 1.0)),
        kind="bbox_edge",
        entity_ref=EntityRef(name="move"),
    )
    target_edge = LineFeature(
        point=Vector((2.0, 5.0, 5.0)),
        direction=Vector((0.0, 0.0, 1.0)),
        kind="bbox_edge",
        entity_ref=EntityRef(name="tgt"),
    )
    rels = solver.solve([moving_edge], [target_edge], ctx)
    x_rel = next(r for r in rels if r.axis == "X")
    assert abs(x_rel.residual - 0.1) < 1e-6
    assert abs(x_rel.delta.translation.x - 0.1) < 1e-6


def test_guide_ticks_produce_two_segments():
    anchor = Vector((0.0, 0.0, 0.0))
    extent = Vector((2.0, 0.0, 0.0))
    direction = Vector((1.0, 0.0, 0.0))
    ticks = guide_ticks(anchor, extent, direction, size=0.2)
    assert len(ticks) == 2
    for seg in ticks:
        assert (seg[1] - seg[0]).length > 0.0


def test_endpoint_tick_is_perpendicular_to_guide():
    tick = endpoint_ticks(Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), size=0.2)
    seg = tick[1] - tick[0]
    assert abs(seg.dot(Vector((1.0, 0.0, 0.0)))) < 1e-5


# Blender's Object.bound_box corner order (swaps 2<->3 and 6<->7 vs ours).
_BLENDER_BOUND_BOX = [
    (-1.0, -1.0, -1.0),
    (-1.0, -1.0, 1.0),
    (-1.0, 1.0, 1.0),
    (-1.0, 1.0, -1.0),
    (1.0, -1.0, -1.0),
    (1.0, -1.0, 1.0),
    (1.0, 1.0, 1.0),
    (1.0, 1.0, -1.0),
]


def test_blender_bound_box_edges_are_axis_aligned():
    from core.bbox import bbox_edges, from_blender_bound_box

    corners = from_blender_bound_box([Vector(c) for c in _BLENDER_BOUND_BOX])
    edges = bbox_edges(corners)
    assert len(edges) == 12
    for a, b in edges:
        # A real box edge changes exactly one coordinate (no face diagonals).
        assert sum(1 for i in range(3) if abs(a[i] - b[i]) > 1e-9) == 1


def test_blender_bound_box_face_centers_include_top_and_bottom():
    from core.bbox import from_blender_bound_box

    corners = from_blender_bound_box([Vector(c) for c in _BLENDER_BOUND_BOX])
    centers = {tuple(round(v, 6) for v in c) for c in bbox_face_centers(corners)}
    assert centers == {
        (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0), (0.0, 1.0, 0.0),
        (0.0, 0.0, -1.0), (0.0, 0.0, 1.0),
    }
