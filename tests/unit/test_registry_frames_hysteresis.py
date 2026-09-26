"""Registry dispatch, frame axes, scoring/NMS, hysteresis, and spatial indexes."""

import core.solvers  # noqa: F401  # populate solver registry
from core.features import FeaturePool, FeatureType, PointFeature, PointKind
from core.frames import Frame, matrix_axes, view_axes, world_axes
from core.registry import clear_registry, dispatch, register_solver
from core.scoring import RankItem, rank, relationship_score
from core.solvers.alignment import AlignmentSolver
from core.solvers.base import SolveContext
from core.spatial import HashGridIndex, PointIndex, broad_phase, build_point_index
from core.tolerance import SnapHysteresis
from mathutils import Matrix, Vector


def _pt(co, kind=PointKind.ORIGIN, entity="A"):
    return PointFeature.from_name(Vector(co), kind, entity)


def test_registry_dispatch_respects_enabled_families():
    clear_registry()
    register_solver(AlignmentSolver())
    moving = FeaturePool(points=[_pt((2.0, 3.0, 0.0), entity="move")])
    targets = FeaturePool(points=[_pt((0.0, 1.0, 0.0), entity="tgt")])
    ctx = SolveContext(axes=world_axes(), world_tol=5.0)

    enabled = dispatch(moving, targets, ctx, {"alignment"})
    disabled = dispatch(moving, targets, ctx, set())
    assert len(enabled) == 3
    assert disabled == []


def test_alignment_consumes_point_pairs():
    solver = AlignmentSolver()
    assert solver.consumes(FeatureType.POINT, FeatureType.POINT)
    assert not solver.consumes(FeatureType.LINE, FeatureType.POINT)


def test_local_frame_axes_from_matrix():
    m = Matrix.Rotation(1.5708, 4, "Z")
    axes = matrix_axes(m)
    assert axes["X"].dot(Vector((0.0, 1.0, 0.0))) > 0.99


def test_view_axes_from_view_matrix():
    vm = Matrix.Rotation(0.5, 4, "Y")
    axes = view_axes(vm)
    assert len(axes) == 3
    for direction in axes.values():
        assert abs(direction.length - 1.0) < 1e-5


def test_relationship_score_prefers_tighter_residual():
    from core.relationship import ConstraintDelta, GuideLine, Relationship

    rel_loose = Relationship(
        family="alignment",
        axis="X",
        label="X",
        moving=_pt((2.0, 3.0, 0.0)),
        targets=(_pt((0.0, 1.0, 0.0), entity="tgt"),),
        residual=2.0,
        delta=ConstraintDelta.from_vector(Vector((0.0, -2.0, 0.0))),
        guide=GuideLine(point=Vector((0.0, 1.0, 0.0)), direction=Vector((1.0, 0.0, 0.0))),
    )
    rel_tight = Relationship(
        family="alignment",
        axis="X",
        label="X",
        moving=_pt((2.0, 1.1, 0.0)),
        targets=(_pt((0.0, 1.0, 0.0), entity="tgt"),),
        residual=0.1,
        delta=ConstraintDelta.from_vector(Vector((0.0, -0.1, 0.0))),
        guide=GuideLine(point=Vector((0.0, 1.0, 0.0)), direction=Vector((1.0, 0.0, 0.0))),
    )
    assert relationship_score(rel_tight, 10.0, 48.0, 5.0) > relationship_score(
        rel_loose, 10.0, 48.0, 5.0
    )


def test_rank_nms_does_not_suppress_across_composable_axes():
    """Orthogonal alignment axes in the same screen cluster all survive NMS."""
    items = [
        RankItem(
            key=("alignment", "X", "A"),
            score=200.0,
            screen_dist=10.0,
            payload="a",
            screen_anchor=(100.0, 100.0),
        ),
        RankItem(
            key=("alignment", "Y", "B"),
            score=150.0,
            screen_dist=12.0,
            payload="b",
            screen_anchor=(105.0, 102.0),
        ),
        RankItem(
            key=("alignment", "Z", "C"),
            score=100.0,
            screen_dist=15.0,
            payload="c",
            screen_anchor=(200.0, 100.0),
        ),
    ]
    ranked, _visible = rank(items, passive_px=48.0, top_k=3, nms_px=20.0)
    assert [it.payload for it in ranked] == ["a", "b", "c"]


def test_rank_nms_still_suppresses_same_axis_competing_targets():
    """Competing guides that share an axis slot keep only the higher score."""
    items = [
        RankItem(
            key=("alignment", "X", "A"),
            score=200.0,
            screen_dist=10.0,
            payload="a",
            screen_anchor=(100.0, 100.0),
        ),
        RankItem(
            key=("alignment", "X", "B"),
            score=150.0,
            screen_dist=12.0,
            payload="b",
            screen_anchor=(105.0, 102.0),
        ),
    ]
    ranked, _visible = rank(items, passive_px=48.0, top_k=3, nms_px=20.0)
    assert [it.payload for it in ranked] == ["a"]


def test_snap_hysteresis_latches_and_releases():
    snap = SnapHysteresis()
    items = [
        RankItem(key=("alignment", "X", "A"), score=1.0, screen_dist=8.0, payload=1),
    ]
    active, snapped = snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    assert snapped and active.payload == 1

    # Still latched within release band (12 + 4 = 16).
    items[0] = RankItem(
        key=("alignment", "X", "A"), score=1.0, screen_dist=14.0, payload=1
    )
    active, snapped = snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    assert snapped and active.screen_dist == 14.0

    # Beyond release distance: latch breaks.
    items[0] = RankItem(
        key=("alignment", "X", "A"), score=1.0, screen_dist=20.0, payload=1
    )
    active, snapped = snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    assert not snapped and active is None


def test_snap_hysteresis_break_requires_leaving_snap_zone():
    snap = SnapHysteresis()
    items = [
        RankItem(key=("alignment", "X", "A"), score=1.0, screen_dist=8.0, payload=1),
    ]
    snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    items[0] = RankItem(
        key=("alignment", "X", "A"), score=1.0, screen_dist=20.0, payload=1
    )
    snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    items[0] = RankItem(
        key=("alignment", "X", "A"), score=1.0, screen_dist=8.0, payload=1
    )
    active, snapped = snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    assert not snapped
    items[0] = RankItem(
        key=("alignment", "X", "A"), score=1.0, screen_dist=17.0, payload=1
    )
    snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    items[0] = RankItem(
        key=("alignment", "X", "A"), score=1.0, screen_dist=8.0, payload=1
    )
    active, snapped = snap.pick_active(items, snap_px=12.0, hysteresis_px=4.0)
    assert snapped and active.payload == 1


def test_hash_grid_index_matches_point_index_radius():
    items = [
        (_pt((0.0, 0.0, 0.0)).co, "a"),
        (_pt((1.0, 0.0, 0.0)).co, "b"),
        (_pt((10.0, 0.0, 0.0)).co, "c"),
    ]
    kdt = PointIndex(items)
    grid = HashGridIndex(items, cell_size=1.0)
    center = Vector((0.5, 0.0, 0.0))
    assert set(kdt.query_radius(center, 1.0)) == set(grid.query_radius(center, 1.0))


def test_broad_phase_falls_back_to_nearest():
    items = [(_pt((100.0, 0.0, 0.0)).co, "far")]
    index = build_point_index(items, strategy="hash", cell_size=5.0)
    found = broad_phase(index, Vector((0.0, 0.0, 0.0)), passive_world=0.01)
    assert found == ["far"]


def test_snap_hysteresis_holds_latch_when_not_in_top_k():
    snap = SnapHysteresis()
    latched = RankItem(
        key=("alignment", "X", "A"),
        score=100.0,
        screen_dist=6.0,
        payload="latched",
    )
    other = RankItem(
        key=("alignment", "Y", "B"),
        score=200.0,
        screen_dist=4.0,
        payload="other",
    )
    visible = [other, latched]
    snap.pick_active([latched], snap_px=12.0, hysteresis_px=4.0, visible=visible)
    active, snapped = snap.pick_active(
        [other], snap_px=12.0, hysteresis_px=4.0, visible=visible
    )
    assert snapped and active.payload == "latched"


def test_solve_context_carries_frame():
    ctx = SolveContext(
        axes=world_axes(),
        world_tol=1.0,
        frame=Frame.LOCAL,
        passive_px=48.0,
        snap_px=12.0,
    )
    assert ctx.frame == Frame.LOCAL


def test_break_blocks_only_the_guide_that_broke():
    """A guide parked in the snap zone must not keep snapping disabled.

    Regression: after any break, re-engaging waited for the *best* candidate
    to leave the zone. A relationship held at a fixed distance (already
    satisfied, or pinned by an axis lock) never leaves, so snapping stayed
    dead for the rest of the drag.
    """
    snap = SnapHysteresis()
    x_key = ("alignment", "X", "A")
    y_key = ("alignment", "Y", "A")
    parked = RankItem(key=y_key, score=1.0, screen_dist=0.0, payload="y")

    snap.pick_active(
        [RankItem(key=x_key, score=1.0, screen_dist=8.0, payload="x")],
        snap_px=12.0, hysteresis_px=4.0,
    )
    # X breaks away while Y sits in the zone.
    snap.pick_active(
        [parked, RankItem(key=x_key, score=1.0, screen_dist=20.0, payload="x")],
        snap_px=12.0, hysteresis_px=4.0,
    )
    # Another guide may engage straight away...
    active, snapped = snap.pick_active([parked], snap_px=12.0, hysteresis_px=4.0)
    assert snapped and active.payload == "y"


def test_broken_guide_still_needs_to_leave_before_reengaging():
    snap = SnapHysteresis()
    x_key = ("alignment", "X", "A")
    snap.pick_active(
        [RankItem(key=x_key, score=1.0, screen_dist=8.0, payload="x")],
        snap_px=12.0, hysteresis_px=4.0,
    )
    snap.pick_active(
        [RankItem(key=x_key, score=1.0, screen_dist=20.0, payload="x")],
        snap_px=12.0, hysteresis_px=4.0,
    )
    back = RankItem(key=x_key, score=1.0, screen_dist=8.0, payload="x")
    _active, snapped = snap.pick_active([back], snap_px=12.0, hysteresis_px=4.0)
    assert not snapped
