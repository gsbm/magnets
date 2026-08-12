"""Equal-size solver."""

from __future__ import annotations

from ..features import BBoxFeature, FeatureType
from ..relationship import ConstraintDelta, GuideSegment, Relationship
from ..transform import TransformMode
from .base import SolveContext, Solver


class EqualSizeSolver(Solver):
    """Equal bounding-box size solver."""
    family = "equal_size"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.BBOX, FeatureType.BBOX)

    def solve(self, moving: list[BBoxFeature], candidates: list[BBoxFeature], ctx: SolveContext):
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
        axis_names = ("X", "Y", "Z")
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                for idx, axis in enumerate(axis_names):
                    mv = m.dimensions[idx]
                    cv = c.dimensions[idx]
                    if mv <= 1e-9 or cv <= 1e-9:
                        continue
                    residual = abs(mv - cv)
                    if residual > tol:
                        continue
                    if ctx.transform_mode == TransformMode.SCALE and mv > 1e-9:
                        factor = cv / mv
                        delta = ConstraintDelta.from_scale(factor)
                    else:
                        direction = ctx.axes[axis]
                        shift = direction * ((cv - mv) * 0.5)
                        delta = ConstraintDelta.from_vector(shift)
                    direction = ctx.axes[axis]
                    out.append(
                        Relationship(
                            family=self.family,
                            axis=f"size_{axis}",
                            label=f"▭ {axis} · {cv * ctx.unit_scale:.3f}",
                            moving=m,
                            targets=(c,),
                            residual=residual,
                            delta=delta,
                            guide=GuideSegment(
                                a=c.center - direction * cv * 0.5,
                                b=c.center + direction * cv * 0.5,
                            ),
                        )
                    )
        return out
