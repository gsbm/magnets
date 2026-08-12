"""Solver ABC and shared ``SolveContext``."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from mathutils import Vector

from ..features import FeatureType
from ..frames import Frame
from ..relationship import Relationship
from ..transform import TransformMode


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


class Solver(ABC):
    """Abstract geometric constraint solver."""

    family: str

    def consumes(self, a: FeatureType, b: FeatureType) -> bool:
        """True if this solver handles the unordered feature-type pair.

        Args:
            a: First feature type.
            b: Second feature type.

        Returns:
            Whether the pair is accepted.
        """
        want = self.feature_types()
        return (a, b) == want or (b, a) == want

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Moving and candidate feature types this solver expects."""
        return (FeatureType.POINT, FeatureType.POINT)

    @abstractmethod
    def solve(
        self,
        moving,
        candidates,
        ctx: SolveContext,
    ) -> list[Relationship]:
        """Evaluate ``moving`` against ``candidates`` and return relationships.

        Args:
            moving: Features from the transformed selection.
            candidates: Nearby static features of the paired type.
            ctx: Shared solve parameters.

        Returns:
            Zero or more candidate relationships.
        """
