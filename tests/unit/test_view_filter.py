"""View-plane guide visibility (2D orthographic views)."""

from core.features import PointFeature, PointKind
from core.relationship import ConstraintDelta, GuideLine, Relationship
from core.view_filter import (
    filter_relationships_for_view,
    guide_direction_visible,
    relationship_visible_in_view,
    restrict_snap_axes,
)
from mathutils import Vector


def _rel(axis, direction, constraint_dir=None):
    return Relationship(
        family="alignment",
        axis=axis,
        label=axis,
        moving=PointFeature.from_name(Vector((0.0, 0.0, 0.0)), PointKind.ORIGIN, "m"),
        targets=(PointFeature.from_name(Vector((1.0, 0.0, 0.0)), PointKind.ORIGIN, "t"),),
        residual=0.1,
        delta=ConstraintDelta.from_vector(Vector((0.0, 0.0, 0.0))),
        guide=GuideLine(point=Vector((0.0, 0.0, 0.0)), direction=direction),
        constraint_dir=constraint_dir,
    )


_AXES = {"X": Vector((1.0, 0.0, 0.0)), "Y": Vector((0.0, 1.0, 0.0)), "Z": Vector((0.0, 0.0, 1.0))}


def _solver_alignment(axis, view_normal):
    """Alignment as ``AlignmentSolver`` builds it: the guide joins the two points
    across their shared coordinate, so it lies *perpendicular* to its snap axis
    (here chosen in the view plane when possible).
    """
    snap_axis = _AXES[axis]
    guide_dir = snap_axis.cross(view_normal)
    if guide_dir.length_squared < 1e-12:  # snap axis along the depth
        guide_dir = snap_axis.orthogonal()
    return _rel(axis, guide_dir.normalized(), constraint_dir=snap_axis)


def test_guide_parallel_to_view_normal_hidden():
    view_normal = Vector((0.0, 0.0, 1.0))  # top view, looking down +Z
    assert not guide_direction_visible(Vector((0.0, 0.0, 1.0)), view_normal)
    assert guide_direction_visible(Vector((1.0, 0.0, 0.0)), view_normal)
    assert guide_direction_visible(Vector((0.0, 1.0, 0.0)), view_normal)


def test_relationship_filter_top_view_hides_z_alignment():
    view_normal = Vector((0.0, 0.0, 1.0))
    rels = [
        _rel("X", Vector((1.0, 0.0, 0.0))),
        _rel("Y", Vector((0.0, 1.0, 0.0))),
        _rel("Z", Vector((0.0, 0.0, 1.0))),
    ]
    visible = filter_relationships_for_view(rels, view_normal)
    axes = {rel.axis for rel in visible}
    assert axes == {"X", "Y"}


def test_relationship_filter_front_view_hides_y():
    view_normal = Vector((0.0, -1.0, 0.0))  # front view
    rels = [
        _rel("X", Vector((1.0, 0.0, 0.0))),
        _rel("Y", Vector((0.0, 1.0, 0.0))),
        _rel("Z", Vector((0.0, 0.0, 1.0))),
    ]
    visible = filter_relationships_for_view(rels, view_normal)
    axes = {rel.axis for rel in visible}
    assert axes == {"X", "Z"}


def test_perspective_skips_filter():
    rel = _rel("Z", Vector((0.0, 0.0, 1.0)))
    assert relationship_visible_in_view(rel, None)
    assert filter_relationships_for_view([rel], None) == [rel]


def test_restrict_snap_axes_drops_disabled_alignment_axes_only():
    rels = [
        _rel("X", Vector((1.0, 0.0, 0.0))),
        _rel("Y", Vector((0.0, 1.0, 0.0))),
        _rel("Z", Vector((0.0, 0.0, 1.0))),
    ]
    other = Relationship(
        family="spacing",
        axis="gap_A",
        label="=",
        moving=PointFeature.from_name(Vector((0.0, 0.0, 0.0)), PointKind.ORIGIN, "m"),
        targets=(PointFeature.from_name(Vector((1.0, 0.0, 0.0)), PointKind.ORIGIN, "t"),),
        residual=0.1,
        delta=ConstraintDelta.from_vector(Vector((0.0, 0.0, 0.0))),
        guide=GuideLine(point=Vector((0.0, 0.0, 0.0)), direction=Vector((1.0, 0.0, 0.0))),
    )
    kept = restrict_snap_axes(rels + [other], {"X", "Y"})
    assert {r.axis for r in kept if r.family == "alignment"} == {"X", "Y"}
    assert other in kept


def test_top_view_hides_alignment_snapping_along_depth():
    """Same height (Z) is invisible from the top and the commit drops it anyway."""
    top = Vector((0.0, 0.0, -1.0))
    rels = [_solver_alignment(a, top) for a in ("X", "Y", "Z")]
    visible = filter_relationships_for_view(rels, top)
    assert {rel.axis for rel in visible} == {"X", "Y"}


def test_front_and_side_views_hide_their_depth_axis():
    front_n, side_n = Vector((0.0, 1.0, 0.0)), Vector((-1.0, 0.0, 0.0))
    front = filter_relationships_for_view(
        [_solver_alignment(a, front_n) for a in ("X", "Y", "Z")], front_n
    )
    side = filter_relationships_for_view(
        [_solver_alignment(a, side_n) for a in ("X", "Y", "Z")], side_n
    )
    assert {rel.axis for rel in front} == {"X", "Z"}
    assert {rel.axis for rel in side} == {"Y", "Z"}


def test_oblique_ortho_view_keeps_every_axis():
    view_normal = Vector((1.0, 1.0, 1.0)).normalized()
    rels = [_solver_alignment(a, view_normal) for a in ("X", "Y", "Z")]
    assert len(filter_relationships_for_view(rels, view_normal)) == 3
