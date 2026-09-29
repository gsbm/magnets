"""Concentric solver."""

from __future__ import annotations

from ..features import CircleFeature, FeatureType
from ..geometry import normalize
from ..relationship import ConstraintDelta, GuideCircle, Relationship
from .base import SolveContext, Solver


class ConcentricSolver(Solver):
    """Concentric circle solver."""
    family = "concentric"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        return (FeatureType.CIRCLE, FeatureType.CIRCLE)

    def solve(
        self,
        moving: list[CircleFeature],
        candidates: list[CircleFeature],
        ctx: SolveContext,
    ):
        out: list[Relationship] = []
        tol = ctx.world_tol
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                if abs(normalize(m.normal).dot(normalize(c.normal))) < 0.9:
                    continue
                residual = (m.center - c.center).length
                if residual > tol:
                    continue
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"con_{c.entity}",
                        label="",  # the icon says it
                        moving=m,
                        targets=(c,),
                        residual=residual,
                        delta=ConstraintDelta.from_vector(c.center - m.center),
                        guide=GuideCircle(
                            center=c.center.copy(),
                            normal=c.normal.copy(),
                            radius=c.radius,
                        ),
                    )
                )
        return out
