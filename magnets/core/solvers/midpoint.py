"""Midpoint solver."""

from __future__ import annotations

from ..features import FeatureType, PointFeature
from ..relationship import ConstraintDelta, GuideSegment, Relationship
from .base import SolveContext, Solver


class MidpointSolver(Solver):
    """Midpoint between two features of one target object.

    Only same-kind pairs count (corner-corner gives edge midpoints, vertex-
    vertex gives edge midpoints in Edit Mode). Mixed pairs such as origin +
    face center land on points with no geometric meaning. Centering between
    *two different objects* is the distribution solver's job.
    """
    family = "midpoint"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.POINT)

    def solve(self, moving: list[PointFeature], candidates: list[PointFeature], ctx: SolveContext):
        """Return relationships between ``moving`` and ``candidates`` features."""
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
                        if a.kind != b.kind:
                            continue
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
