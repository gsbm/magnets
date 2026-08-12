"""3D View orientation helpers (requires bpy at call site)."""

from __future__ import annotations

from mathutils import Vector

from ..core.relationship import Relationship
from ..core.view_filter import filter_relationships_for_view


def view_normal_world(rv3d) -> Vector | None:
    """World-space camera look direction, or None in perspective / invalid view.

    In orthographic 2D axis views this is ±X, ±Y, or ±Z. Guides aligned with
    this direction are edge-on and should be ignored.
    """
    if rv3d is None or rv3d.is_perspective:
        return None
    try:
        inv = rv3d.view_matrix.inverted()
    except Exception:
        return None
    forward = (-inv.col[2].to_3d())
    if forward.length_squared < 1e-12:
        return None
    return forward.normalized()


def filter_for_view(rels: list[Relationship], rv3d) -> list[Relationship]:
    """Drop relationships whose guides are invisible in the view.

    Args:
        rels: Candidate relationships.
        rv3d: RegionView3D (or None to keep all).

    Returns:
        Filtered relationship list.
    """
    return filter_relationships_for_view(rels, view_normal_world(rv3d))
