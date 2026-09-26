"""Scene unit scale for projected distance labels."""

from __future__ import annotations


def scene_unit_info(context) -> tuple[float, str]:
    """Return ``(scale, suffix)`` for displaying world-unit distances.

    Blender's unit scale maps one Blender Unit to ``unit_settings.scale_length``
    real-world units. We show distances in meters by default.
    """
    scale = context.scene.unit_settings.scale_length or 1.0
    system = context.scene.unit_settings.system

    if system == "IMPERIAL":
        # scale_length is still meters internally; label in feet for display.
        return (scale * 3.28084, "ft")
    if system == "NONE":
        return (scale, "bu")
    return (scale, "m")


def length_formatter(context):
    """Return a callable formatting world lengths in the scene's units.

    Uses Blender's own unit display (``1.2 mm``, ``4.84"``, ``2.5 km``) so guide
    labels read like the rest of the UI. Returns None when unavailable, which
    makes labels fall back to plain numbers.
    """
    try:
        from bpy.utils import units
    except ImportError:  # pragma: no cover - always present inside Blender
        return None

    settings = context.scene.unit_settings
    system = settings.system
    scale = settings.scale_length or 1.0

    def fmt(value: float) -> str:
        try:
            return units.to_string(system, "LENGTH", value * scale, precision=3).strip()
        except (ValueError, TypeError):
            return f"{value * scale:.3f}"

    return fmt
