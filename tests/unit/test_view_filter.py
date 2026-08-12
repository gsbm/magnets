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


def _rel(axis, direction):
    return Relationship(
        family="alignment",
        axis=axis,
        label=axis,
        moving=PointFeature.from_name(Vector((0.0, 0.0, 0.0)), PointKind.ORIGIN, "m"),
        targets=(PointFeature.from_name(Vector((1.0, 0.0, 0.0)), PointKind.ORIGIN, "t"),),
        residual=0.1,
        delta=ConstraintDelta.from_vector(Vector((0.0, 0.0, 0.0))),
        guide=GuideLine(point=Vector((0.0, 0.0, 0.0)), direction=direction),
    )


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
