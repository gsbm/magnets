"""Parallel solver for lines and directions."""

from __future__ import annotations

from ..features import DirectionFeature, FeatureType, LineFeature
from ..geometry import lines_parallel, normalize
from ..relationship import ConstraintDelta, GuideLine, Relationship
from .base import SolveContext, Solver


class ParallelSolver(Solver):
    """Parallel line solver."""
    family = "parallel"

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
                if not lines_parallel(m.direction, c.direction, angle_tol=0.08):
                    continue
                w = m.point - c.point
                d = normalize(c.direction)
                residual = (w - d * w.dot(d)).length
                if residual > tol:
                    continue
                correction = c.point - m.point
                correction = correction - d * correction.dot(d)
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"par_{c.entity}",
                        label="",  # the icon says it
                        moving=m,
                        targets=(c,),
                        residual=residual,
                        delta=ConstraintDelta.from_vector(correction),
                        guide=GuideLine(point=c.point.copy(), direction=c.direction.copy()),
                    )
                )
        return out


class DirectionParallelSolver(Solver):
    """Parallel direction solver."""
    family = "parallel"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.DIRECTION, FeatureType.DIRECTION)

    def solve(
        self,
        moving: list[DirectionFeature],
        candidates: list[DirectionFeature],
        ctx: SolveContext,
    ):
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                if not lines_parallel(m.direction, c.direction, angle_tol=0.08):
                    continue
                residual = (m.origin - c.origin).cross(normalize(m.direction)).length
                if residual > tol:
                    continue
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"dpar_{c.entity}",
                        label="",  # the icon says it
                        moving=m,
                        targets=(c,),
                        residual=residual,
                        delta=ConstraintDelta.from_vector(c.origin - m.origin),
                        guide=GuideLine(point=c.origin.copy(), direction=c.direction.copy()),
                    )
                )
        return out
