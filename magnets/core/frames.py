"""Coordinate frames.

Maps a ``Frame`` name to an axis basis (X/Y/Z unit directions in world space).
"""

from __future__ import annotations

from enum import Enum

from mathutils import Matrix, Vector


class Frame(Enum):
    """Reference frame used for axis-aligned snaps."""
    WORLD = "world"
    LOCAL = "local"
    VIEW = "view"
    PARENT = "parent"
    COLLECTION = "collection"
    CUSTOM = "custom"


WORLD_AXES: dict[str, Vector] = {
    "X": Vector((1.0, 0.0, 0.0)),
    "Y": Vector((0.0, 1.0, 0.0)),
    "Z": Vector((0.0, 0.0, 1.0)),
}


def _axis_dict(x: Vector, y: Vector, z: Vector) -> dict[str, Vector]:
    return {
        "X": x.normalized() if x.length_squared else Vector((1.0, 0.0, 0.0)),
        "Y": y.normalized() if y.length_squared else Vector((0.0, 1.0, 0.0)),
        "Z": z.normalized() if z.length_squared else Vector((0.0, 0.0, 1.0)),
    }


def world_axes() -> dict[str, Vector]:
    """Return a copy of the world X/Y/Z basis."""
    return {k: v.copy() for k, v in WORLD_AXES.items()}


def matrix_axes(matrix: Matrix) -> dict[str, Vector]:
    """Column basis vectors from a 4×4 transform (rotation + scale)."""
    return _axis_dict(matrix.col[0].to_3d(), matrix.col[1].to_3d(), matrix.col[2].to_3d())


def view_axes(view_matrix: Matrix) -> dict[str, Vector]:
    """View-aligned axes expressed in world space."""
    inv = view_matrix.inverted()
    return _axis_dict(inv.col[0].to_3d(), inv.col[1].to_3d(), inv.col[2].to_3d())
