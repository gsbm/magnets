"""Coplanar solver: point on plane."""

from __future__ import annotations

from ..features import FeatureType, PlaneFeature, PointFeature
from ..geometry import distance_point_plane, normalize
from ..relationship import ConstraintDelta, GuidePlane, Relationship
from .base import SolveContext, Solver


class CoplanarSolver(Solver):
    """Point-on-plane coplanarity solver."""
    family = "coplanar"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.PLANE)

    def solve(
        self,
        moving: list[PointFeature],
        candidates: list[PlaneFeature],
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
                residual = distance_point_plane(m.co, c.point, c.normal)
                if residual > tol:
                    continue
                n = normalize(c.normal)
                signed = (m.co - c.point).dot(n)
                desired = m.co - n * signed
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"cop_{c.entity}",
                        label="▭",
                        moving=m,
                        targets=(c,),
                        residual=residual,
                        delta=ConstraintDelta.from_vector(desired - m.co),
                        guide=GuidePlane(point=c.point.copy(), normal=c.normal.copy()),
                    )
                )
        return out
