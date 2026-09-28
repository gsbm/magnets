"""Solver ABC and shared ``SolveContext``."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from mathutils import Vector

from ..features import FeatureType
from ..frames import Frame
from ..labels import LengthFormat, format_length
from ..relationship import Relationship
from ..transform import TransformMode
from ..view_filter import guide_direction_visible


@dataclass
class SolveContext:
    """Shared parameters passed to every solver invocation."""

    axes: dict[str, Vector]
    world_tol: float
    frame: Frame = Frame.WORLD
    passive_px: float = 48.0
    snap_px: float = 12.0
    unit_scale: float = 1.0
    surface_query_limit: int = 8
    transform_mode: TransformMode = TransformMode.TRANSLATE
    # Distribution gap metric: "center", "edge", or "both".
    spacing_metric: str = "both"
    # Scene-aware length formatter for labels (e.g. "12.3 cm"); None falls back
    # to a plain number scaled by ``unit_scale``.
    length_format: LengthFormat | None = None
    # World view direction of an orthographic view (None in perspective).
    # Solvers may skip what ``view_filter`` would hide in this view anyway.
    view_normal: Vector | None = None

    def direction_hidden(self, direction: Vector) -> bool:
        """True when the view filter hides a snap/guide along ``direction``."""
        if self.view_normal is None:
            return False
        return not guide_direction_visible(direction, self.view_normal)

    def format_length(self, value: float) -> str:
        """Format a world-space length for a guide label."""
        return format_length(value, self.unit_scale, self.length_format)


class Solver(ABC):
    """Abstract geometric constraint solver."""

    family: str

    def consumes(self, a: FeatureType, b: FeatureType) -> bool:
        """Return True if this solver handles the unordered pair ``(a, b)``."""
        want = self.feature_types()
        return (a, b) == want or (b, a) == want

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver expects."""
        return (FeatureType.POINT, FeatureType.POINT)

    @abstractmethod
    def solve(
        self,
        moving,
        candidates,
        ctx: SolveContext,
    ) -> list[Relationship]:
        """Evaluate ``moving`` against ``candidates`` and return relationships."""
