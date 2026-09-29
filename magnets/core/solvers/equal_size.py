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
        return (FeatureType.BBOX, FeatureType.BBOX)

    def solve(self, moving: list[BBoxFeature], candidates: list[BBoxFeature], ctx: SolveContext):
        """Return relationships between ``moving`` and ``candidates`` features.

        Scale only: a move or rotate cannot change size, and a same-size
        neighbour would otherwise engage at 0 px and hold the X/Y/Z snap slot
        for the whole drag, blocking real alignments.
        """
        out: list[Relationship] = []
        if ctx.transform_mode != TransformMode.SCALE:
            return out
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
                    delta = ConstraintDelta.from_scale(cv / mv)
                    direction = ctx.axes[axis]
                    out.append(
                        Relationship(
                            family=self.family,
                            axis=f"size_{axis}",
                            label=f"{axis} · {ctx.format_length(cv)}",
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
