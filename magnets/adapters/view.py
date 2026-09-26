"""3D View orientation helpers (requires bpy at call site)."""

from __future__ import annotations

from mathutils import Vector

from ..core.relationship import Relationship
from ..core.view_filter import filter_relationships_for_view


def view_normal_world(rv3d) -> Vector | None:
    """Return the world view direction in orthographic views, else None.

    Guides parallel to it are edge-on and should be ignored.
    """
    if rv3d is None or rv3d.is_perspective:
        return None
    try:
        inv = rv3d.view_matrix.inverted()
    except ValueError:  # singular view matrix
        return None
    forward = (-inv.col[2].to_3d())
    if forward.length_squared < 1e-12:
        return None
    return forward.normalized()


def filter_for_view(rels: list[Relationship], rv3d) -> list[Relationship]:
    """Drop relationships whose guides are invisible in ``rv3d`` (None keeps all)."""
    return filter_relationships_for_view(rels, view_normal_world(rv3d))


def ui_scale(context) -> float:
    """Return Blender's UI scale (display scale x OS DPI) for custom drawing.

    Screen-space sizes are authored at 1x and multiplied by this to match the
    UI on HiDPI screens. Headless Blender reports 0, so fall back to 1.
    """
    try:
        return float(context.preferences.system.ui_scale) or 1.0
    except AttributeError:
        return 1.0


def pixel_size(context) -> float:
    """Suggested line thickness multiplier for custom drawing."""
    try:
        return float(context.preferences.system.pixel_size) or 1.0
    except AttributeError:
        return 1.0
