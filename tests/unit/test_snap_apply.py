"""Snap apply mode and multi-axis distance tests."""

from core.scoring import RankItem
from core.snap_apply import (
    BREAK,
    BREAK_BAND,
    HOLD,
    masked_translation,
    max_active_screen_dist,
    project_out_direction,
    snap_apply_mode,
)
from mathutils import Vector


def test_masked_translation_unconstrained_is_identity():
    assert masked_translation(Vector((1.0, 2.0, 3.0)), None) == Vector((1.0, 2.0, 3.0))


def test_masked_translation_single_axis_lock():
    # G X: only the X component of the snap survives.
    assert masked_translation(Vector((1.0, 2.0, 3.0)), (True, False, False)) == Vector(
        (1.0, 0.0, 0.0)
    )


def test_masked_translation_plane_lock():
    # G Shift+Z excludes Z: X and Y survive.
    assert masked_translation(Vector((1.0, 2.0, 3.0)), (True, True, False)) == Vector(
        (1.0, 2.0, 0.0)
    )


def test_project_out_axis_aligned_normal_drops_that_axis():
    # Orthographic front view (looking along Y): the Y snap component is dropped,
    # leaving a clean 2-axis (X, Z) correction.
    out = project_out_direction(Vector((1.0, 2.0, 3.0)), Vector((0.0, 1.0, 0.0)))
    assert out == Vector((1.0, 0.0, 3.0))


def test_project_out_perspective_uses_full_vector():
    # The overlay only projects in orthographic views; here we simply assert the
    # projection is a no-op when the correction is already in-plane.
    out = project_out_direction(Vector((1.0, 0.0, 3.0)), Vector((0.0, 1.0, 0.0)))
    assert out == Vector((1.0, 0.0, 3.0))


def test_project_out_non_unit_normal_is_normalized():
    out = project_out_direction(Vector((1.0, 2.0, 3.0)), Vector((0.0, 5.0, 0.0)))
    assert out == Vector((1.0, 0.0, 3.0))


def test_project_out_tilted_normal_removes_component():
    n = Vector((1.0, 1.0, 0.0))
    out = project_out_direction(Vector((1.0, 1.0, 0.0)), n)
    # (1,1,0) is entirely along the normal, so nothing remains in-plane.
    assert out.length < 1e-9


def test_project_out_zero_normal_is_identity():
    out = project_out_direction(Vector((1.0, 2.0, 3.0)), Vector((0.0, 0.0, 0.0)))
    assert out == Vector((1.0, 2.0, 3.0))


def test_snap_apply_mode_zones():
    assert snap_apply_mode(10.0, 16.0, 56.0) == HOLD
    assert snap_apply_mode(20.0, 16.0, 56.0) == BREAK_BAND
    assert snap_apply_mode(60.0, 16.0, 56.0) == BREAK


def test_max_active_screen_dist_uses_worst_axis():
    keys = {("alignment", "X", "A"), ("alignment", "Y", "B")}
    items = [
        RankItem(key=("alignment", "X", "A"), score=1.0, screen_dist=5.0, payload="x"),
        RankItem(key=("alignment", "Y", "B"), score=1.0, screen_dist=22.0, payload="y"),
    ]
    assert max_active_screen_dist(keys, items) == 22.0
