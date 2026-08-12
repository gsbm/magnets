"""Transform mode enum for modal operators."""

from __future__ import annotations

from enum import Enum


class TransformMode(Enum):
    """Active transform modality for solvers."""
    TRANSLATE = "translate"
    ROTATE = "rotate"
    SCALE = "scale"
    EXTRUDE = "extrude"
