"""Midpoint solver."""

from __future__ import annotations

from ..features import FeatureType, PointFeature
from ..relationship import ConstraintDelta, GuideSegment, Relationship
from .base import BestPerKey, SolveContext, Solver


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
        """Return the best relationship per rank key (see ``BestPerKey``)."""
        tol = ctx.world_tol
        # Same-kind pairs per entity and their midpoints do not depend on the
        # moving point: build them once, in the original visiting order.
        by_entity: dict[str, list[PointFeature]] = {}
        for c in candidates:
            by_entity.setdefault(c.entity_ref.name, []).append(c)
        pairs_by_entity: list[tuple[str, list]] = []
        for name, pts in by_entity.items():
            pairs = []
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    a, b = pts[i], pts[j]
                    if a.kind == b.kind:
                        pairs.append((a, b, (a.co + b.co) * 0.5))
            if pairs:
                pairs_by_entity.append((name, pairs))
        best = BestPerKey()
        for m in moving:
            for name, pairs in pairs_by_entity:
                if name == m.entity_ref.name:
                    continue
                for a, b, mid in pairs:
                    residual = (m.co - mid).length
                    if residual > tol:
                        continue
                    if ctx.direction_hidden(b.co - a.co):
                        continue  # an end-on guide segment is filtered out anyway
                    order = ctx.rank_order(self.family, m, residual, m.co, mid - m.co)
                    best.offer((name, id(m.kind), id(a.kind)), order, (m, a, b, residual, mid))
        return [self._relationship(*data) for data in best.winners()]

    def _relationship(self, m, a, b, residual, mid) -> Relationship:
        return Relationship(
            family=self.family,
            axis=f"mid_{a.entity}_{b.entity}",
            label="◇",
            moving=m,
            targets=(a, b),
            residual=residual,
            delta=ConstraintDelta.from_vector(mid - m.co),
            guide=GuideSegment(a=a.co.copy(), b=b.co.copy()),
        )
