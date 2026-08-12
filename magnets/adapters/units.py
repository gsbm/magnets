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
