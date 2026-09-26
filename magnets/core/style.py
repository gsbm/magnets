"""Guide colour and emphasis rules (no bpy).

Kept pure so the look of engaged vs approaching guides is unit-testable.
"""

from __future__ import annotations

Color = tuple[float, float, float, float]

# Engaged guides draw thicker than approaching ones so the state change reads
# even for colour-blind users or low-contrast themes.
ACTIVE_WIDTH_SCALE = 1.75

# Engage pulse: a short, time-based flash (redraw-rate independent).
PULSE_DURATION_S = 0.18
PULSE_WIDTH_BOOST = 1.0    # extra width multiplier at the pulse peak
PULSE_WHITE_MIX = 0.45     # blend toward white at the pulse peak

_AXES = ("X", "Y", "Z")


def engaged_color(
    family: str,
    axis: str,
    *,
    use_axis_colors: bool,
    active_color: Color,
    axis_colors: dict[str, Color] | None,
) -> Color:
    """Colour for an engaged guide.

    With axis colours on, an alignment guide takes the theme colour of the axis
    it aligns on (X red, Y green, Z blue, like Blender's gizmos); every other
    relationship uses the active colour.
    """
    if use_axis_colors and axis_colors and family == "alignment" and axis in _AXES:
        color = axis_colors.get(axis)
        if color is not None:
            return color
    return active_color


def pulse_strength(elapsed_s: float, duration_s: float = PULSE_DURATION_S) -> float:
    """Pulse intensity in [0, 1]: 1 at engage, fading linearly to 0."""
    if duration_s <= 0.0 or elapsed_s < 0.0 or elapsed_s >= duration_s:
        return 0.0
    return 1.0 - elapsed_s / duration_s


def pulsed_color(color: Color, strength: float) -> Color:
    """Brighten ``color`` toward white by the pulse strength."""
    if strength <= 0.0:
        return color
    mix = PULSE_WHITE_MIX * min(strength, 1.0)
    r, g, b, a = color
    return (r + (1.0 - r) * mix, g + (1.0 - g) * mix, b + (1.0 - b) * mix, a)


def pulsed_width(width: float, strength: float) -> float:
    """Widen a line by the pulse strength."""
    if strength <= 0.0:
        return width
    return width * (1.0 + PULSE_WIDTH_BOOST * min(strength, 1.0))
