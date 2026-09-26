"""Perpendicular solver."""

from __future__ import annotations

from mathutils import Vector

from ..features import FeatureType, LineFeature
from ..geometry import lines_perpendicular, normalize
from ..relationship import ConstraintDelta, GuideLine, Relationship
from .base import SolveContext, Solver


class PerpendicularSolver(Solver):
    """Perpendicular line/direction solver."""
    family = "perpendicular"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.LINE, FeatureType.LINE)

    def solve(self, moving: list[LineFeature], candidates: list[LineFeature], ctx: SolveContext):
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                if not lines_perpendicular(m.direction, c.direction, angle_tol=0.08):
                    continue
                residual = abs(normalize(m.direction).dot(normalize(c.direction)))
                if residual > 0.08:
                    continue
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"perp_{c.entity}",
                        label="⊥",
                        moving=m,
                        targets=(c,),
                        residual=residual * tol,
                        delta=ConstraintDelta.from_vector(Vector((0.0, 0.0, 0.0))),
                        guide=GuideLine(point=c.point.copy(), direction=c.direction.copy()),
                    )
                )
        return out
