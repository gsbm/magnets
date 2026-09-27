"""Sticky-snap grace/break paths, direction-parallel snaps, scene unit info."""

from types import SimpleNamespace

from adapters.units import scene_unit_info
from core.features import DirectionFeature, EntityRef, FeaturePool, FeatureType
from core.frames import world_axes
from core.scoring import RankItem
from core.solvers.base import SolveContext
from core.solvers.parallel import DirectionParallelSolver
from core.tolerance import SnapHysteresis
from mathutils import Vector

A = ("alignment", "X", "A")
B = ("alignment", "Y", "B")
FAR = ("alignment", "Z", "far")


def _item(key, dist):
    return RankItem(key=key, score=1.0, screen_dist=dist, payload=key)


def _pick(snap, ranked, visible=None):
    return snap.pick_active(
        ranked, snap_px=12.0, hysteresis_px=4.0, visible=visible, reengage_margin_px=4.0
    )


# ── SnapHysteresis ───────────────────────────────────────────────────────────


def test_hysteresis_holds_latch_for_three_missing_frames():
    """A guide that drops out for a few frames stays engaged, then breaks."""
    snap = SnapHysteresis()
    assert _pick(snap, [_item(A, 8.0)]) == (_item(A, 8.0), True)

    others = [_item(FAR, 40.0)]
    for _ in range(3):
        active, snapped = _pick(snap, others)
        assert snapped and active.key == A, "grace frames keep the last latch"

    assert _pick(snap, others) == (None, False), "4th missing frame breaks"
    assert snap.broken and snap.active_key is None
    # The culprit is still absent, so the next frame clears the break.
    assert _pick(snap, others) == (None, False)
    assert snap.broken is False


def test_hysteresis_grace_counter_resets_when_guide_returns():
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 8.0)])
    others = [_item(FAR, 40.0)]
    for _ in range(3):
        _pick(snap, others)
    assert _pick(snap, [_item(A, 9.0)])[1], "guide is back before the 4th miss"
    for _ in range(3):
        assert _pick(snap, others)[1], "miss counter restarted"


def test_hysteresis_vanished_latch_yields_to_guide_in_zone():
    """After a jump, a new in-zone guide takes over instead of the grace hold."""
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 0.0)])
    active, snapped = _pick(snap, [_item(B, 7.5)])
    assert snapped and active.key == B
    assert snap.active_key == B and snap._miss_frames == 0
    # Out of the zone, a new guide does not steal the grace hold.
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 0.0)])
    active, snapped = _pick(snap, [_item(B, 14.0)])
    assert snapped and active.key == A


def test_hysteresis_visible_list_holds_latch_outside_top_k():
    """Falling out of the decluttered top-K alone must not drop the latch."""
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 8.0)])
    active, snapped = _pick(snap, [_item(B, 30.0)], visible=[_item(B, 30.0), _item(A, 10.0)])
    assert snapped and active.key == A and active.screen_dist == 10.0


def test_hysteresis_other_guide_engages_while_culprit_is_blocked():
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 8.0)])
    assert _pick(snap, [_item(A, 20.0)]) == (None, False)  # breaks away (> 16)
    assert snap.broken

    # A comes back into the snap zone: blocked. B in the zone engages instead.
    active, snapped = _pick(snap, [_item(A, 5.0), _item(B, 10.0)])
    assert snapped and active.key == B
    assert snap.broken, "A stays blocked until it leaves the re-engage band"


def test_hysteresis_culprit_must_leave_reengage_band():
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 8.0)])
    _pick(snap, [_item(A, 20.0)])
    # 15 px is inside snap + margin (16): still blocked.
    assert _pick(snap, [_item(A, 15.0)]) == (None, False)
    assert _pick(snap, [_item(A, 8.0)]) == (None, False)
    # Leaving the band (> 16) clears the break; next frame may engage.
    assert _pick(snap, [_item(A, 17.0)]) == (None, False)
    assert not snap.broken
    assert _pick(snap, [_item(A, 8.0)])[1]


def test_hysteresis_unknown_culprit_blocks_until_best_leaves():
    """force_break with nothing latched blocks all guides until the best leaves."""
    snap = SnapHysteresis()
    snap.force_break()
    assert snap.broken and snap._broken_key is None

    assert _pick(snap, [_item(A, 5.0), _item(B, 6.0)]) == (None, False)
    assert _pick(snap, [], visible=[_item(B, 6.0)]) == (None, False), (
        "falls back to the visible list when nothing is ranked"
    )
    assert _pick(snap, [_item(A, 30.0)]) == (None, False)
    assert not snap.broken
    assert _pick(snap, [_item(B, 6.0)])[1]


def test_hysteresis_empty_frame_resets_everything():
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 8.0)])
    snap.remember_active_keys({A})
    assert _pick(snap, []) == (None, False)
    assert snap.active_key is None and not snap.broken and snap.sticky_keys == set()


def test_hysteresis_sticky_keys():
    snap = SnapHysteresis()
    snap.remember_active_keys({A, B})
    snap.remember_active_keys(set())
    assert snap.sticky_keys == {A, B}, "an empty set does not clear sticky keys"
    snap.active_key = A
    snap.force_break()
    assert snap.sticky_keys == set(), "a break forgets sticky keys"
    assert snap._broken_key == A


def test_hysteresis_nothing_in_zone_returns_none():
    snap = SnapHysteresis()
    assert _pick(snap, [_item(A, 13.0)]) == (None, False)
    assert snap.active_key is None and not snap.broken


# ── DirectionParallelSolver ──────────────────────────────────────────────────


def _dir(origin, direction, entity):
    return DirectionFeature(Vector(origin), Vector(direction), "light_axis", EntityRef(entity))


def _ctx(tol=1.0):
    return SolveContext(axes=world_axes(), world_tol=tol, unit_scale=1.0)


def test_direction_parallel_snaps_onto_candidate_axis():
    solver = DirectionParallelSolver()
    assert solver.feature_types() == (FeatureType.DIRECTION, FeatureType.DIRECTION)
    moving = [_dir((0.0, 0.3, 5.0), (0.0, 0.0, 1.0), "lamp")]
    cand = [_dir((0.0, 0.0, 0.0), (0.0, 0.0, -1.0), "cam")]  # anti-parallel counts
    rels = solver.solve(moving, cand, _ctx())
    assert len(rels) == 1
    rel = rels[0]
    assert rel.family == "parallel" and rel.axis == "dpar_cam"
    assert abs(rel.residual - 0.3) < 1e-6, "offset between the two axes"
    assert (rel.delta.translation - Vector((0.0, -0.3, -5.0))).length < 1e-6
    assert (rel.guide.point - Vector((0, 0, 0))).length < 1e-9


def test_direction_parallel_rejects_non_matches():
    solver = DirectionParallelSolver()
    moving = [_dir((0.0, 0.3, 0.0), (0.0, 0.0, 1.0), "lamp")]
    assert solver.solve(moving, [_dir((0, 0, 0), (1, 0, 0), "cam")], _ctx()) == [], "not parallel"
    assert solver.solve(moving, [_dir((0, 0, 0), (0, 0, 1), "lamp")], _ctx()) == [], "same entity"
    assert solver.solve(moving, [_dir((0, 5, 0), (0, 0, 1), "cam")], _ctx()) == [], "too far"


def test_feature_pool_routes_directions():
    d = _dir((0, 0, 0), (0, 0, 1), "lamp")
    pool = FeaturePool(directions=[d])
    assert pool.by_type(FeatureType.DIRECTION) == [d]


# ── scene_unit_info ──────────────────────────────────────────────────────────


def _unit_ctx(system, scale):
    return SimpleNamespace(
        scene=SimpleNamespace(unit_settings=SimpleNamespace(system=system, scale_length=scale))
    )


def test_scene_unit_info_per_system():
    assert scene_unit_info(_unit_ctx("METRIC", 2.0)) == (2.0, "m")
    assert scene_unit_info(_unit_ctx("NONE", 0.5)) == (0.5, "bu")
    scale, suffix = scene_unit_info(_unit_ctx("IMPERIAL", 1.0))
    assert suffix == "ft" and abs(scale - 3.28084) < 1e-9


def test_scene_unit_info_zero_scale_falls_back_to_one():
    assert scene_unit_info(_unit_ctx("METRIC", 0.0)) == (1.0, "m")


def test_hysteresis_band_hold_yields_to_guide_in_zone():
    """A guide held only by the hysteresis band loses to one inside the zone."""
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 6.0)])
    active, snapped = _pick(snap, [_item(A, 14.0), _item(B, 3.5)])
    assert snapped and active.key == B, "the in-zone guide takes over"
    # Inside the snap zone the latch keeps its guide (no flicker between two).
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 6.0)])
    active, _ = _pick(snap, [_item(A, 10.0), _item(B, 3.5)])
    assert active.key == A
    # No rival: the band keeps holding.
    snap = SnapHysteresis()
    _pick(snap, [_item(A, 6.0)])
    active, snapped = _pick(snap, [_item(A, 15.0), _item(B, 20.0)])
    assert snapped and active.key == A
