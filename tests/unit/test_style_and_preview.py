"""Guide styling (engaged colours, pulse), preview labels, dash capping."""

import math

from core.labels import rotation_snap_label, size_match_label
from core.style import (
    ACTIVE_WIDTH_SCALE,
    engaged_color,
    pulse_strength,
    pulsed_color,
    pulsed_width,
)
from core.transform_snap import equal_size_scale, nearest_size_match
from draw.glyphs import dash_segments
from mathutils import Vector

_ACTIVE = (1.0, 0.2, 0.75, 1.0)
_AXES = {"X": (1.0, 0.2, 0.3, 1.0), "Y": (0.5, 0.9, 0.0, 1.0), "Z": (0.2, 0.5, 1.0, 1.0)}


# ── Engaged colours ──────────────────────────────────────────────────────────

def test_alignment_guide_takes_its_axis_color():
    for axis, color in _AXES.items():
        got = engaged_color(
            "alignment", axis, use_axis_colors=True, active_color=_ACTIVE, axis_colors=_AXES
        )
        assert got == color


def test_non_alignment_guides_use_active_color():
    got = engaged_color(
        "spacing", "X", use_axis_colors=True, active_color=_ACTIVE, axis_colors=_AXES
    )
    assert got == _ACTIVE


def test_single_color_mode_ignores_axis_colors():
    got = engaged_color(
        "alignment", "X", use_axis_colors=False, active_color=_ACTIVE, axis_colors=_AXES
    )
    assert got == _ACTIVE


def test_missing_theme_falls_back_to_active_color():
    got = engaged_color(
        "alignment", "Y", use_axis_colors=True, active_color=_ACTIVE, axis_colors=None
    )
    assert got == _ACTIVE


def test_engaged_guides_draw_thicker():
    assert ACTIVE_WIDTH_SCALE > 1.0


# ── Pulse ────────────────────────────────────────────────────────────────────

def test_pulse_is_time_based_and_fades_out():
    assert pulse_strength(0.0) == 1.0
    assert 0.0 < pulse_strength(0.09) < 1.0
    assert pulse_strength(10.0) == 0.0
    assert pulse_strength(-1.0) == 0.0


def test_pulse_brightens_and_widens_then_restores():
    bright = pulsed_color(_ACTIVE, 1.0)
    assert all(b >= a for a, b in zip(_ACTIVE[:3], bright[:3]))
    assert bright[3] == _ACTIVE[3]
    assert pulsed_color(_ACTIVE, 0.0) == _ACTIVE
    assert pulsed_width(2.0, 1.0) > 2.0
    assert pulsed_width(2.0, 0.0) == 2.0


# ── Preview labels ───────────────────────────────────────────────────────────

def test_rotation_label_trims_trailing_zeros():
    assert rotation_snap_label(math.radians(45.0)) == "→ 45°"
    assert rotation_snap_label(math.radians(7.5)) == "→ 7.5°"


def test_size_match_label_names_the_neighbour():
    assert size_match_label("Cube.002", "2 m") == "= Cube.002 · 2 m"


# ── Scale target ─────────────────────────────────────────────────────────────

def test_nearest_size_match_reports_the_matched_neighbour():
    match = nearest_size_match(2.0, [("Small", 3.0), ("Big", 5.0)], world_tol=1.5)
    assert match is not None
    name, size, factor = match
    assert (name, size) == ("Small", 3.0)
    assert abs(factor - 1.5) < 1e-9


def test_nearest_size_match_agrees_with_equal_size_scale():
    cands = [("A", 3.0), ("B", 5.0)]
    match = nearest_size_match(4.6, cands, world_tol=1.0)
    assert match is not None
    assert equal_size_scale(4.6, [3.0, 5.0], world_tol=1.0) == match[2]
    assert nearest_size_match(2.0, [("B", 5.0)], world_tol=1.0) is None


# ── Dashes ───────────────────────────────────────────────────────────────────

def test_dash_count_is_capped_on_very_long_lines():
    a, b = Vector((0.0, 0.0, 0.0)), Vector((10000.0, 0.0, 0.0))
    dashes = dash_segments(a, b, dash=0.1, gap=0.1, max_count=100)
    assert len(dashes) <= 101
    # Dashes still cover the whole line.
    assert dashes[-1][1].x > 9800.0


def test_dash_segments_uncapped_by_default():
    a, b = Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0))
    assert len(dash_segments(a, b, dash=0.1, gap=0.1)) == 5
