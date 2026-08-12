"""Symmetry solver."""

from __future__ import annotations

from ..features import FeatureType, PointFeature
from ..geometry import reflect_point
from ..relationship import ConstraintDelta, GuidePlane, Relationship
from .base import SolveContext, Solver

_SYMMETRY_PLANES = (
    ("XY", "Z"),
    ("XZ", "Y"),
    ("YZ", "X"),
)


class SymmetrySolver(Solver):
    """Reflection symmetry solver."""
    family = "symmetry"

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
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                mid = (m.co + c.co) * 0.5
                for plane_name, axis_key in _SYMMETRY_PLANES:
                    normal = ctx.axes[axis_key]
                    reflected = reflect_point(m.co, mid, normal)
                    residual = (reflected - c.co).length
                    if residual > tol:
                        continue
                    out.append(
                        Relationship(
                            family=self.family,
                            axis=f"sym_{plane_name}_{c.entity}",
                            label=f"⇔ {plane_name}",
                            moving=m,
                            targets=(c,),
                            residual=residual,
                            delta=ConstraintDelta.from_vector(c.co - m.co),
                            guide=GuidePlane(point=mid.copy(), normal=normal.copy()),
                        )
                    )
        return out
