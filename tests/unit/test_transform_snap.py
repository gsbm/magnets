"""Release-time rotate/scale snap and adaptive timer interval helpers."""

import math

from core.transform_snap import (
    adaptive_interval,
    equal_size_scale,
    rotated_matrix,
    scaled_matrix,
    snap_rotation_delta,
)
from mathutils import Matrix, Vector

_BASE = 1.0 / 120.0


def _rot_z(deg: float) -> Matrix:
    return Matrix.Rotation(math.radians(deg), 4, "Z")


# ── snap_rotation_delta ──────────────────────────────────────────────────────

def test_rotation_snap_disabled_when_increment_zero():
    assert snap_rotation_delta(Matrix.Identity(4), _rot_z(44), 0.0) is None


def test_rotation_snap_engages_near_increment():
    snap = snap_rotation_delta(Matrix.Identity(4), _rot_z(43), 45.0)
    assert snap is not None
    axis, angle = snap
    assert math.isclose(angle, math.radians(45), rel_tol=1e-6)
    # 43° about +Z snaps around the +Z axis.
    assert axis.z > 0.99


def test_rotation_snap_skips_deliberate_off_increment_angle():
    # 22° is nearest to 0 (not 45), so there is no meaningful increment to snap.
    assert snap_rotation_delta(Matrix.Identity(4), _rot_z(22), 45.0) is None


def test_rotation_snap_noop_when_already_on_increment():
    assert snap_rotation_delta(Matrix.Identity(4), _rot_z(90), 45.0) is None


def test_rotation_snap_respects_start_orientation():
    # Net rotation is 88 - 45 = 43°, which snaps to a 45° net → total 90° here is
    # measured from start, so the returned total is the snapped *delta*.
    start = _rot_z(45)
    final = _rot_z(88)
    snap = snap_rotation_delta(start, final, 45.0)
    assert snap is not None
    _axis, angle = snap
    assert math.isclose(angle, math.radians(45), rel_tol=1e-6)


# ── equal_size_scale ─────────────────────────────────────────────────────────

def test_equal_size_snaps_to_nearest_candidate():
    factor = equal_size_scale(2.0, [3.0, 5.0], world_tol=1.5)
    assert factor is not None
    assert math.isclose(factor, 1.5, rel_tol=1e-9)


def test_equal_size_none_when_no_candidate_in_tol():
    assert equal_size_scale(2.0, [5.0], world_tol=1.0) is None


def test_equal_size_none_when_already_matching():
    assert equal_size_scale(3.0, [3.0], world_tol=1.0) is None


def test_equal_size_ignores_degenerate_inputs():
    assert equal_size_scale(0.0, [3.0], world_tol=1.0) is None
    assert equal_size_scale(2.0, [], world_tol=1.0) is None
    assert equal_size_scale(2.0, [3.0], world_tol=0.0) is None


# ── rotated_matrix / scaled_matrix ───────────────────────────────────────────

def test_rotated_matrix_about_origin():
    m = Matrix.Translation((1.0, 0.0, 0.0))
    out = rotated_matrix(m, Vector((0.0, 0.0, 1.0)), math.radians(90), Vector((0, 0, 0)))
    assert (out.translation - Vector((0.0, 1.0, 0.0))).length < 1e-6


def test_scaled_matrix_moves_origin_from_pivot():
    m = Matrix.Translation((2.0, 0.0, 0.0))
    out = scaled_matrix(m, 2.0, Vector((0.0, 0.0, 0.0)))
    assert (out.translation - Vector((4.0, 0.0, 0.0))).length < 1e-6


def test_scaled_matrix_scales_the_basis():
    out = scaled_matrix(Matrix.Identity(4), 3.0, Vector((0.0, 0.0, 0.0)))
    _loc, _rot, scale = out.decompose()
    assert (scale - Vector((3.0, 3.0, 3.0))).length < 1e-6


# ── adaptive_interval ────────────────────────────────────────────────────────

def test_throttle_stays_at_base_under_budget():
    assert adaptive_interval(0.001, base=_BASE, budget_s=0.008) == _BASE


def test_throttle_grows_with_cost():
    out = adaptive_interval(0.02, base=_BASE, budget_s=0.008)
    assert math.isclose(out, 0.03, rel_tol=1e-9)


def test_throttle_capped_at_ceiling():
    assert adaptive_interval(0.2, base=_BASE, budget_s=0.008, ceiling_s=0.1) == 0.1
