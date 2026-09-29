"""Coplanar solver: point on plane."""

from __future__ import annotations

from ..features import FeatureType, PlaneFeature, PointFeature
from ..geometry import distance_point_plane, normalize
from ..relationship import ConstraintDelta, GuidePlane, Relationship
from .base import BestPerKey, SolveContext, Solver


class CoplanarSolver(Solver):
    """Point-on-plane coplanarity solver."""
    family = "coplanar"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        return (FeatureType.POINT, FeatureType.PLANE)

    def solve(
        self,
        moving: list[PointFeature],
        candidates: list[PlaneFeature],
        ctx: SolveContext,
    ):
        """Return the best relationship per rank key (see ``BestPerKey``)."""
        tol = ctx.world_tol
        best = BestPerKey()
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                residual = distance_point_plane(m.co, c.point, c.normal)
                if residual > tol:
                    continue
                if ctx.direction_hidden(c.normal):
                    continue  # a plane snapping along the view depth is filtered anyway
                best.offer((c.entity_ref.name, id(m.kind), c.kind), residual, (m, c, residual))
        return [self._relationship(*data) for data in best.winners()]

    def _relationship(self, m, c, residual) -> Relationship:
        n = normalize(c.normal)
        signed = (m.co - c.point).dot(n)
        desired = m.co - n * signed
        return Relationship(
            family=self.family,
            axis=f"cop_{c.entity}",
            label="",  # the icon says it
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(desired - m.co),
            guide=GuidePlane(point=c.point.copy(), normal=c.normal.copy()),
            constraint_dir=n.copy(),
        )
