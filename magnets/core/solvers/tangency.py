"""Tangency and surface-offset solver."""

from __future__ import annotations

from ..features import CircleFeature, FeatureType, PointFeature, SurfaceFeature
from ..geometry import normalize
from ..relationship import ConstraintDelta, GuideCircle, GuideLine, Relationship
from .base import SolveContext, Solver


class TangencySolver(Solver):
    """Circle tangency solver."""
    family = "tangency"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.CIRCLE, FeatureType.CIRCLE)

    def solve(self, moving: list[CircleFeature], candidates: list[CircleFeature], ctx: SolveContext):
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                if abs(m.normal.dot(c.normal)) < 0.9:
                    continue
                center_delta = c.center - m.center
                dist = center_delta.length
                for target_dist in (m.radius + c.radius, abs(m.radius - c.radius)):
                    residual = abs(dist - target_dist)
                    if residual > tol:
                        continue
                    if dist > tol:
                        direction = center_delta / dist
                        desired = c.center - direction * target_dist
                    else:
                        desired = c.center - normalize(c.normal) * target_dist
                    out.append(
                        Relationship(
                            family=self.family,
                            axis=f"tan_{c.entity}",
                            label="◎",
                            moving=m,
                            targets=(c,),
                            residual=residual,
                            delta=ConstraintDelta.from_vector(desired - m.center),
                            guide=GuideCircle(
                                center=c.center.copy(),
                                normal=c.normal.copy(),
                                radius=c.radius,
                            ),
                        )
                    )
        return out


class SurfaceTangencySolver(Solver):
    """Point-to-surface tangency / offset using BVH samples."""

    family = "tangency"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.SURFACE)

    def solve(
        self,
        moving: list[PointFeature],
        candidates: list[SurfaceFeature],
        ctx: SolveContext,
    ):
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        count = 0
        for m in moving:
            for s in candidates:
                if count >= ctx.surface_query_limit:
                    return out
                count += 1
                if s.entity_ref.name == m.entity_ref.name:
                    continue
                n = normalize(s.normal)
                offset = (m.co - s.point).dot(n)
                residual = abs(offset)
                if residual > tol:
                    continue
                desired = s.point.copy()
                out.append(
                    Relationship(
                        family=self.family,
                        axis=f"surf_{s.entity}",
                        label="↔ surf",
                        moving=m,
                        targets=(s,),
                        residual=residual,
                        delta=ConstraintDelta.from_vector(desired - m.co),
                        guide=GuideLine(point=s.point.copy(), direction=n),
                    )
                )
        return out
