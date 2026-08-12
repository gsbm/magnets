"""Collinear solver: point on line."""

from __future__ import annotations

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import distance_point_line, project_point_on_line
from ..relationship import ConstraintDelta, GuideLine, Relationship
from .base import SolveContext, Solver


class CollinearSolver(Solver):
    """Point-on-line collinearity solver."""
    family = "collinear"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.LINE)

    def solve(
        self,
        moving: list[PointFeature],
        candidates: list[LineFeature],
        ctx: SolveContext,
    ):
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
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                residual = distance_point_line(m.co, c.point, c.direction)
                if residual > tol:
                    continue
                proj = project_point_on_line(m.co, c.point, c.direction)
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"col_{c.entity}",
                        label="-",
                        moving=m,
                        targets=(c,),
                        residual=residual,
                        delta=ConstraintDelta.from_vector(proj - m.co),
                        guide=GuideLine(point=c.point.copy(), direction=c.direction.copy()),
                    )
                )
        return out
