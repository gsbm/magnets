"""Midpoint solver."""

from __future__ import annotations

from ..features import FeatureType, PointFeature
from ..relationship import ConstraintDelta, GuideSegment, Relationship
from .base import SolveContext, Solver


class MidpointSolver(Solver):
    """Midpoint-between-targets solver."""
    family = "midpoint"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.POINT)

    def solve(self, moving: list[PointFeature], candidates: list[PointFeature], ctx: SolveContext):
        """Evaluate moving features against candidates.

        Args:
            moving: Features from the transformed selection.
            candidates: Nearby static features.
            ctx: Shared solve parameters.

        Returns:
            Candidate relationships.
        """
        out: list[Relationship] = []
        tol = ctx.world_tol
        for m in moving:
            by_entity: dict[str, list[PointFeature]] = {}
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                by_entity.setdefault(c.entity_ref.name, []).append(c)
            for pts in by_entity.values():
                if len(pts) < 2:
                    continue
                for i in range(len(pts)):
                    for j in range(i + 1, len(pts)):
                        a, b = pts[i], pts[j]
                        mid = (a.co + b.co) * 0.5
                        residual = (m.co - mid).length
                        if residual > tol:
                            continue
                        out.append(
                            Relationship(
                                family=self.family,
                                axis=f"mid_{a.entity}_{b.entity}",
                                label="◇",
                                moving=m,
                                targets=(a, b),
                                residual=residual,
                                delta=ConstraintDelta.from_vector(mid - m.co),
                                guide=GuideSegment(a=a.co.copy(), b=b.co.copy()),
                            )
                        )
        return out
