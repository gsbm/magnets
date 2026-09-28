"""Collinear solver: point on line."""

from __future__ import annotations

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import distance_point_line, project_point_on_line
from ..relationship import ConstraintDelta, GuideLine, Relationship
from .base import BestPerKey, SolveContext, Solver


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
        """Return the best relationship per rank key (see ``BestPerKey``)."""
        tol = ctx.world_tol
        best = BestPerKey()
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                residual = distance_point_line(m.co, c.point, c.direction)
                if residual > tol:
                    continue
                if ctx.direction_hidden(c.direction):
                    continue  # an end-on guide line is filtered out anyway
                best.offer((c.entity_ref.name, id(m.kind), c.kind), residual, (m, c, residual))
        return [self._relationship(*data) for data in best.winners()]

    def _relationship(self, m, c, residual) -> Relationship:
        proj = project_point_on_line(m.co, c.point, c.direction)
        return Relationship(
            family=self.family,
            axis=f"col_{c.entity}",
            label="-",
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(proj - m.co),
            guide=GuideLine(point=c.point.copy(), direction=c.direction.copy()),
        )
