"""Guide drawing: axis-routed alignment guides, label stacking, lock masks."""

from core.frames import world_axes
from core.guide_draw import axis_route
from core.labels import spread_labels
from core.snap_apply import inferred_axis_mask
from mathutils import Vector

AXES = list(world_axes().values())


def _dirs(segs):
    return [tuple(round(abs(c)) for c in (b - a).normalized()) for a, b in segs]


def test_route_is_one_segment_when_one_axis_differs():
    # X alignment, points differ along Y only: a single Y segment.
    segs = axis_route(Vector((3, 5, 0)), Vector((3, 0, 0)), Vector((1, 0, 0)), AXES)
    assert _dirs(segs) == [(0, 1, 0)]


def test_route_is_an_l_along_frame_axes_with_vertical_leg_last():
    # X alignment with a higher target: along Y at the target's height, then
    # down Z to the mover. Never a slanted line.
    target, mover = Vector((3, 5, 2.5)), Vector((3.2, 0, 0))
    segs = axis_route(target, mover, Vector((1, 0, 0)), AXES)
    assert _dirs(segs) == [(0, 1, 0), (0, 0, 1)]
    assert (segs[0][0] - target).length < 1e-6
    # The mover is projected onto the shared plane (x = 3).
    assert (segs[-1][1] - Vector((3, 0, 0))).length < 1e-6


def test_route_overshoot_extends_both_outer_ends():
    segs = axis_route(Vector((0, 4, 0)), Vector((0, 0, 0)), Vector((1, 0, 0)), AXES, overshoot=0.5)
    (a, b), = segs
    assert abs((b - a).length - 5.0) < 1e-6


def test_route_is_empty_when_points_coincide_in_the_plane():
    assert axis_route(Vector((1, 2, 3)), Vector((1.4, 2, 3)), Vector((1, 0, 0)), AXES) == []


def test_labels_that_overlap_stack_downwards():
    boxes = [(10.0, 100.0, 50.0, 20.0), (20.0, 105.0, 50.0, 20.0), (300.0, 100.0, 40.0, 20.0)]
    out = spread_labels(boxes, gap=2.0)
    # The higher box keeps its place; the other moves just below it.
    assert out[1] == (20.0, 105.0)
    assert out[0] == (10.0, 105.0 - 20.0 - 2.0)
    assert out[2] == (300.0, 100.0), "a label with no overlap does not move"


def test_lock_is_inferred_from_axes_that_did_not_move():
    start = (1.0, 2.0, 3.0)
    assert inferred_axis_mask(start, (1.5, 2.0, 3.0), 0.01) == (True, False, False)  # G X
    assert inferred_axis_mask(start, (1.5, 2.4, 3.0), 0.01) == (True, True, False)  # Shift+Z
    assert inferred_axis_mask(start, (1.5, 2.4, 3.1), 0.01) is None  # free
    assert inferred_axis_mask(start, (1.001, 2.0, 3.0), 0.01) is None  # not moved yet


def test_move_in_the_view_plane_is_not_read_as_a_lock():
    start = (1.0, 2.0, 3.0)
    top = (0.0, 0.0, 1.0)
    # A hand drag straight across the top view leaves Y unchanged: still free.
    assert inferred_axis_mask(start, (1.5, 2.0, 3.0), 0.01, top) is None
    assert inferred_axis_mask(start, (1.5, 2.4, 3.0), 0.01, top) is None
    # Leaving the view plane can only come from a lock (G Z in the top view).
    assert inferred_axis_mask(start, (1.0, 2.0, 3.5), 0.01, top) == (False, False, True)
    # In a tilted view, G X leaves the view plane and is still detected.
    tilted = (0.5, -0.5, 0.707)
    assert inferred_axis_mask(start, (1.5, 2.0, 3.0), 0.01, tilted) == (True, False, False)


def test_lock_mask_drops_guides_pulling_along_locked_axes():
    from core.features import PointFeature, PointKind
    from core.relationship import ConstraintDelta, GuideLine, Relationship
    from core.view_filter import restrict_to_axis_mask

    p = PointFeature.from_name(Vector((0, 0, 0)), PointKind.ORIGIN, "M")

    def rel(axis, d):
        return Relationship(
            family="alignment", axis=axis, label="", moving=p, targets=(p,), residual=0.0,
            delta=ConstraintDelta.from_vector(Vector(d)),
            guide=GuideLine(point=Vector((0, 0, 0)), direction=Vector((0, 1, 0))),
            constraint_dir=Vector(d).normalized(),
        )

    kept = restrict_to_axis_mask([rel("X", (1, 0, 0)), rel("Z", (0, 0, 1))], (True, True, False))
    assert [r.axis for r in kept] == ["X"], "Shift+Z: no Z guide"
