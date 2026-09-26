"""Scene unit scale for projected distance labels."""

from __future__ import annotations


def scene_unit_info(context) -> tuple[float, str]:
    """Return ``(scale, suffix)`` for displaying world-unit distances."""
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

    Uses Blender's unit display (``1.2 mm``, ``2.5 km``) so labels match the UI.
    Returns None when unavailable; labels then fall back to plain numbers.
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
