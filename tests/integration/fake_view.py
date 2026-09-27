"""Synthetic 3D viewports for headless tests (no window in ``--background``).

``region`` / ``rv3d`` stand-ins carrying exactly what ``bpy_extras.view3d_utils``
and Magnets read: the view, window and perspective matrices, ``is_perspective``,
``view_perspective`` and ``view_rotation``.
"""

import math
from types import SimpleNamespace

from mathutils import Matrix

REGION = SimpleNamespace(width=1000, height=1000)
_ORTHO_HALF = 10.0  # orthographic views span 20 world units over 1000 px


def make_rv3d(cam_rot: Matrix, cam_pos, perspective: bool):
    """View looking down the camera's -Z from ``cam_pos`` with ``cam_rot``."""
    cam = Matrix.Translation(cam_pos) @ cam_rot.to_4x4()
    view = cam.inverted()
    if perspective:
        f = 1.0 / math.tan(math.radians(50.0) / 2.0)
        near, far = 0.1, 1000.0
        win = Matrix((
            (f, 0.0, 0.0, 0.0),
            (0.0, f, 0.0, 0.0),
            (0.0, 0.0, (far + near) / (near - far), 2.0 * far * near / (near - far)),
            (0.0, 0.0, -1.0, 0.0),
        ))
    else:
        win = Matrix.Diagonal((1.0 / _ORTHO_HALF, 1.0 / _ORTHO_HALF, -0.01, 1.0))
    return SimpleNamespace(
        is_perspective=perspective,
        view_perspective="PERSP" if perspective else "ORTHO",
        view_matrix=view,
        window_matrix=win,
        perspective_matrix=win @ view,
        view_rotation=cam_rot.to_quaternion(),
    )


# Looking down -Z: world Z is the depth axis.
TOP = (REGION, make_rv3d(Matrix.Identity(3), (0.0, 0.0, 50.0), perspective=False))
# Looking along +Y: world Y is the depth axis.
FRONT = (REGION, make_rv3d(Matrix.Rotation(math.pi / 2, 3, "X"), (0.0, -50.0, 0.0), False))
# Looking along -X: world X is the depth axis.
RIGHT = (
    REGION,
    make_rv3d(
        Matrix.Rotation(math.pi / 2, 3, "Z") @ Matrix.Rotation(math.pi / 2, 3, "X"),
        (50.0, 0.0, 0.0),
        False,
    ),
)
PERSP = (REGION, make_rv3d(Matrix.Identity(3), (0.0, 0.0, 50.0), perspective=True))
