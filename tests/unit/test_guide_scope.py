"""Which guides run: per transform action, and straight vs diagonal pairs."""

import core.solvers  # noqa: F401 - register solver table
from core.families import FAMILY_IDS, families_for_mode
from core.features import PointFeature, PointKind
from core.frames import world_axes
from core.solvers.base import SolveContext
from core.solvers.midpoint import MidpointSolver
from core.solvers.spacing import SpacingSolver
from core.transform import TransformMode
from mathutils import Vector

ALL = set(FAMILY_IDS)


def _pt(co, entity="A", kind=PointKind.BBOX_CORNER):
    return PointFeature.from_name(Vector(co), kind, entity)


def _ctx(allow_diagonal):
    return SolveContext(axes=world_axes(), world_tol=0.2, allow_diagonal=allow_diagonal)


def test_move_runs_every_translation_family():
    fams = families_for_mode(TransformMode.TRANSLATE, ALL)
    assert "alignment" in fams and "parallel" in fams and "spacing" in fams
    assert "equal_size" not in fams and "perpendicular" not in fams
    assert families_for_mode(TransformMode.EXTRUDE, ALL) == fams


def test_rotate_and_scale_run_only_what_they_can_apply():
    # Rotation snaps to angle increments; no solver result can be applied.
    assert families_for_mode(TransformMode.ROTATE, ALL) == set()
    assert families_for_mode(TransformMode.SCALE, ALL) == {"equal_size"}


def test_disabled_family_stays_off_in_its_action():
    assert families_for_mode(TransformMode.SCALE, ALL - {"equal_size"}) == set()


def _box_corners():
    return [_pt((0, 0, 0)), _pt((2, 0, 0)), _pt((2, 2, 0)), _pt((0, 2, 0))]


def test_midpoint_of_a_diagonal_pair_is_diagonal_only():
    moving = [_pt((1.05, 1.0, 0.0), entity="M", kind=PointKind.ORIGIN)]
    diag = MidpointSolver().solve(moving, _box_corners(), _ctx(True))
    assert diag, "the box diagonal's midpoint is offered with diagonals on"
    assert not MidpointSolver().solve(moving, _box_corners(), _ctx(False))


def test_midpoint_along_an_axis_stays_without_diagonals():
    moving = [_pt((1.05, 0.0, 0.0), entity="M", kind=PointKind.ORIGIN)]
    rels = MidpointSolver().solve(moving, _box_corners(), _ctx(False))
    assert rels
    for rel in rels:
        a, b = rel.targets
        assert (b.co - a.co).normalized().to_tuple(3) in {(1, 0, 0), (-1, 0, 0)}


def test_size_repeat_keeps_only_straight_spans():
    # 4.05 along X repeats the 2 m bottom edge; the diagonal spans are dropped.
    moving = [_pt((4.05, 0.0, 0.0), entity="M", kind=PointKind.ORIGIN)]
    straight = SpacingSolver().solve(moving, _box_corners(), _ctx(False))
    assert straight
    for rel in straight:
        a, b = rel.targets
        d = (b.co - a.co).normalized()
        assert max(abs(c) for c in d) > 0.99, f"diagonal span kept: {a.co} {b.co}"
    # Diagonal spans exist for a point on the box diagonal.
    on_diag = [_pt((4.0, 4.05, 0.0), entity="M", kind=PointKind.ORIGIN)]
    assert SpacingSolver().solve(on_diag, _box_corners(), _ctx(True))
    assert not SpacingSolver().solve(on_diag, _box_corners(), _ctx(False))
