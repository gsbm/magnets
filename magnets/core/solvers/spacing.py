"""Equal-spacing solver for a candidate object's internal span."""

from __future__ import annotations

from ..features import FeatureType, PointFeature
from ..geometry import collinear
from ..relationship import ConstraintDelta, GuideSegment, Relationship
from .base import SolveContext, Solver


class SpacingSolver(Solver):
    """Equal internal-span spacing solver."""
    family = "spacing"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.POINT)

    def solve(self, moving: list[PointFeature], candidates: list[PointFeature], ctx: SolveContext):
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
                        ab = (b.co - a.co).length
                        if ab <= tol:
                            continue
                        if not collinear(a.co, b.co, m.co, tol):
                            continue
                        for target, gap in ((a, (m.co - a.co).length), (b, (m.co - b.co).length)):
                            residual = abs(gap - ab)
                            if residual > tol:
                                continue
                            desired = a.co + (b.co - a.co).normalized() * ab
                            if (desired - m.co).length > ab * 2:
                                desired = b.co + (a.co - b.co).normalized() * ab
                            delta = desired - m.co
                            out.append(
                                Relationship(
                                    family=self.family,
                                    axis=f"gap_{target.entity}",
                                    label=f"= · {ab * ctx.unit_scale:.3f}",
                                    moving=m,
                                    targets=(a, b),
                                    residual=residual,
                                    delta=ConstraintDelta.from_vector(delta),
                                    guide=GuideSegment(a=a.co.copy(), b=b.co.copy()),
                                )
                            )
        return out
