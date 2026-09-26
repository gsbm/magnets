"""Constraint graph, multi-constraint resolve, and transform delta helpers."""

from core.features import PointFeature, PointKind
from core.graph import build_active_set, constraints_compatible, snap_axis_slot
from core.relationship import ConstraintDelta, GuideLine, Relationship
from core.resolver import (
    clamp_translation_step,
    resolve_rotation,
    resolve_scale,
    resolve_translation,
    snap_angle,
)
from core.scoring import RankItem
from mathutils import Vector


def _pt(co, kind=PointKind.ORIGIN, entity="A"):
    return PointFeature.from_name(Vector(co), kind, entity)


def _rel(family, axis, delta, entity="tgt", residual=1.0):
    return Relationship(
        family=family,
        axis=axis,
        label=axis,
        moving=_pt((0.0, 0.0, 0.0), entity="move"),
        targets=(_pt((0.0, 0.0, 0.0), entity=entity),),
        residual=residual,
        delta=delta,
        guide=GuideLine(point=Vector((0.0, 0.0, 0.0)), direction=Vector((1.0, 0.0, 0.0))),
    )


def test_constraints_compatible_orthogonal_alignments():
    ax = _rel("alignment", "X", ConstraintDelta.from_vector(Vector((1.0, 0.0, 0.0))))
    ay = _rel("alignment", "Y", ConstraintDelta.from_vector(Vector((0.0, 1.0, 0.0))))
    assert constraints_compatible(ax, ay)
    assert not constraints_compatible(ax, ax)


def test_constraints_compatible_same_family_axis():
    a = _rel("spacing", "gap_A", ConstraintDelta.from_vector(Vector((1.0, 0.0, 0.0))))
    b = _rel("spacing", "gap_A", ConstraintDelta.from_vector(Vector((2.0, 0.0, 0.0))))
    assert not constraints_compatible(a, b)


def test_snap_axis_slot_collapses_duplicate_alignment_axes():
    a = _rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, 0.0, 0.0))), entity="A")
    b = _rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, 0.0, 0.0))), entity="B")
    assert snap_axis_slot(a) == snap_axis_slot(b) == "alignment:X"


def test_resolve_translation_multi_constraint():
    rel_x = _rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -2.0, 0.0))))
    rel_y = _rel("alignment", "Y", ConstraintDelta.from_vector(Vector((3.0, 0.0, 0.0))))
    result = resolve_translation([rel_x, rel_y])
    assert result == Vector((3.0, -2.0, 0.0))


def test_resolve_translation_skips_duplicate_alignment_axis():
    rel_x1 = _rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -1.0, 0.0))))
    rel_x2 = _rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -5.0, 0.0))))
    result = resolve_translation([rel_x1, rel_x2])
    assert result.y == -1.0


def test_build_active_set_allows_xy_blocks_duplicate_x():
    primary = RankItem(
        key=("alignment", "X", "A"),
        score=100.0,
        screen_dist=5.0,
        payload=_rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -2.0, 0.0))), entity="A"),
    )
    x_other = RankItem(
        key=("alignment", "X", "B"),
        score=95.0,
        screen_dist=6.0,
        payload=_rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -3.0, 0.0))), entity="B"),
    )
    y_item = RankItem(
        key=("alignment", "Y", "C"),
        score=90.0,
        screen_dist=8.0,
        payload=_rel("alignment", "Y", ConstraintDelta.from_vector(Vector((3.0, 0.0, 0.0))), entity="C"),
    )
    active = build_active_set(primary, [primary, x_other, y_item], snap_px=12.0)
    assert len(active) == 2
    assert {rel.axis for rel in active} == {"X", "Y"}
    assert resolve_translation(active) == Vector((3.0, -2.0, 0.0))


def test_build_active_set_keeps_y_when_ranked_by_score_not_distance():
    """Score-sorted ranked list must not drop a valid Y guide after a distant X."""
    primary = RankItem(
        key=("alignment", "X", "A"),
        score=100.0,
        screen_dist=5.0,
        payload=_rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -2.0, 0.0))), entity="A"),
    )
    x_far = RankItem(
        key=("alignment", "X", "B"),
        score=95.0,
        screen_dist=50.0,
        payload=_rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -3.0, 0.0))), entity="B"),
    )
    y_item = RankItem(
        key=("alignment", "Y", "C"),
        score=90.0,
        screen_dist=8.0,
        payload=_rel("alignment", "Y", ConstraintDelta.from_vector(Vector((3.0, 0.0, 0.0))), entity="C"),
    )
    active = build_active_set(
        primary,
        [primary, x_far, y_item],
        snap_px=12.0,
        release_px=16.0,
    )
    assert len(active) == 2
    assert {rel.axis for rel in active} == {"X", "Y"}


def test_build_active_set_composes_compatible():
    primary = RankItem(
        key=("alignment", "X", "A"),
        score=100.0,
        screen_dist=5.0,
        payload=_rel("alignment", "X", ConstraintDelta.from_vector(Vector((0.0, -2.0, 0.0)))),
    )
    secondary = RankItem(
        key=("alignment", "Y", "B"),
        score=90.0,
        screen_dist=8.0,
        payload=_rel("alignment", "Y", ConstraintDelta.from_vector(Vector((3.0, 0.0, 0.0)))),
    )
    active = build_active_set(primary, [primary, secondary], snap_px=12.0)
    assert len(active) == 2
    assert resolve_translation(active) == Vector((3.0, -2.0, 0.0))


def test_constraint_delta_rotation_and_scale():
    rot = ConstraintDelta.from_rotation(Vector((0.0, 0.0, 1.0)), 0.5)
    _axis, angle = resolve_rotation([_rel("parallel", "p", rot)])
    assert angle == 0.5

    scale = ConstraintDelta.from_scale(2.0)
    rel = _rel("equal_size", "size_X", scale)
    assert resolve_scale([rel]) == Vector((2.0, 2.0, 2.0))


def test_clamp_translation_step():
    v = Vector((10.0, 0.0, 0.0))
    clamped = clamp_translation_step(v, 2.0)
    assert clamped.length == 2.0
    assert clamp_translation_step(Vector((0.5, 0.0, 0.0)), 2.0).length == 0.5


def test_snap_angle_degrees():
    import math

    snapped = snap_angle(math.radians(47.0), 15.0)
    assert abs(math.degrees(snapped) - 45.0) < 1e-6


# ── Overlapping constraints: one correction per direction ────────────────────

_X, _Y, _Z = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))


def _aligned(axis, delta, direction):
    rel = _rel("alignment", axis, ConstraintDelta.from_vector(Vector(delta)))
    rel.constraint_dir = direction
    return rel


def test_overlapping_deltas_do_not_stack():
    """Alignment, spacing and midpoint deltas along X apply once, not summed."""
    align_x = _aligned("X", (0.068, 0.0, 0.0), _X)
    align_y = _aligned("Y", (0.0, 0.07, 0.0), _Y)
    align_z = _aligned("Z", (0.0, 0.0, 0.0), _Z)  # already satisfied
    spacing = _rel("spacing", "gap_T", ConstraintDelta.from_vector(Vector((0.1, 0.0, 0.0))))
    midpoint = _rel(
        "midpoint", "mid_T_T", ConstraintDelta.from_vector(Vector((0.035, 0.02, 0.4)))
    )
    result = resolve_translation([midpoint, spacing, align_z, align_x, align_y])
    assert (result - Vector((0.068, 0.07, 0.0))).length < 1e-9


def test_alignment_wins_its_axis_regardless_of_input_order():
    align_x = _aligned("X", (0.1, 0.0, 0.0), _X)
    spacing = _rel("spacing", "gap_T", ConstraintDelta.from_vector(Vector((0.5, 0.0, 0.0))))
    assert resolve_translation([spacing, align_x]) == Vector((0.1, 0.0, 0.0))
    assert resolve_translation([align_x, spacing]) == Vector((0.1, 0.0, 0.0))


def test_satisfied_alignment_holds_its_axis():
    """A zero-residual alignment still claims its axis."""
    align_z = _aligned("Z", (0.0, 0.0, 0.0), _Z)
    midpoint = _rel(
        "midpoint", "mid_T_T", ConstraintDelta.from_vector(Vector((0.0, 0.2, 0.5)))
    )
    assert resolve_translation([midpoint, align_z]) == Vector((0.0, 0.2, 0.0))


def test_lower_priority_keeps_its_orthogonal_part():
    """Gram-Schmidt: only the claimed component is dropped."""
    align_x = _aligned("X", (0.1, 0.0, 0.0), _X)
    midpoint = _rel(
        "midpoint", "mid_T_T", ConstraintDelta.from_vector(Vector((0.3, 0.2, 0.0)))
    )
    assert (resolve_translation([align_x, midpoint]) - Vector((0.1, 0.2, 0.0))).length < 1e-9


def test_non_axis_deltas_claim_their_own_direction():
    """Without ``constraint_dir``, a delta claims its own direction."""
    a = _rel("spacing", "gap_A", ConstraintDelta.from_vector(Vector((0.2, 0.0, 0.0))))
    b = _rel("midpoint", "mid_B_B", ConstraintDelta.from_vector(Vector((0.5, 0.0, 0.0))))
    assert resolve_translation([a, b]) == Vector((0.2, 0.0, 0.0))
