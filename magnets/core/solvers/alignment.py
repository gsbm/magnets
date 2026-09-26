"""Alignment solver: per-axis coordinate matching for points and edges.

Each reference axis is independent. Point and edge variants share family
``alignment`` and the same per-axis snap slot.
"""

from __future__ import annotations

from mathutils import Vector

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import lines_parallel, normalize
from ..labels import alignment_label
from ..relationship import ConstraintDelta, GuideLine, Relationship
from .base import SolveContext, Solver


def _fallback_perp(direction: Vector) -> Vector:
    """A unit vector perpendicular to ``direction`` (for a degenerate guide)."""
    ref = Vector((0.0, 0.0, 1.0)) if abs(direction.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    perp = direction.cross(ref)
    return perp.normalized() if perp.length > 1e-9 else Vector((0.0, 1.0, 0.0))


class AlignmentSolver(Solver):
    """Per-axis point alignment solver."""
    family = "alignment"

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
                w = m.co - c.co
                for axis_name, direction in ctx.axes.items():
                    along = w.dot(direction)
                    residual = abs(along)
                    if residual > tol:
                        continue
                    # Correction: slide the moving point along this axis until
                    # its coordinate matches the candidate's. Other axes untouched.
                    correction = -along * direction
                    # Guide line lies in the shared-coordinate plane, running from
                    # the target through the (aligned) moving point: a vertical
                    # guide for an X match, horizontal for Y, etc.
                    perp = w - along * direction
                    guide_dir = perp.normalized() if perp.length > 1e-6 else _fallback_perp(direction)
                    out.append(
                        Relationship(
                            family=self.family,
                            axis=axis_name,
                            label=alignment_label(
                                axis_name, c.kind, residual, ctx.unit_scale, ctx.length_format
                            ),
                            moving=m,
                            targets=(c,),
                            residual=residual,
                            delta=ConstraintDelta.from_vector(correction),
                            guide=GuideLine(point=c.co.copy(), direction=guide_dir),
                            constraint_dir=direction.normalized(),
                        )
                    )
        return out


class EdgeAlignmentSolver(Solver):
    """Per-axis alignment for parallel edges, the edge counterpart of
    ``AlignmentSolver``. Requires true parallelism (not just a coincidental
    shared coordinate) before an axis engages.
    """

    family = "alignment"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.LINE, FeatureType.LINE)

    def solve(self, moving: list[LineFeature], candidates: list[LineFeature], ctx: SolveContext):
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
            m_dir = normalize(m.direction)
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                if not lines_parallel(m_dir, c.direction, angle_tol=0.08):
                    continue
                w = m.point - c.point
                for axis_name, direction in ctx.axes.items():
                    # An infinite line has no meaningful offset along its own
                    # direction: skip axes the edge runs parallel to.
                    if abs(m_dir.dot(direction)) > 0.9:
                        continue
                    along = w.dot(direction)
                    residual = abs(along)
                    if residual > tol:
                        continue
                    correction = -along * direction
                    perp = w - along * direction
                    guide_dir = perp.normalized() if perp.length > 1e-6 else _fallback_perp(direction)
                    out.append(
                        Relationship(
                            family=self.family,
                            axis=axis_name,
                            label=alignment_label(
                                axis_name, c.kind, residual, ctx.unit_scale, ctx.length_format
                            ),
                            moving=m,
                            targets=(c,),
                            residual=residual,
                            delta=ConstraintDelta.from_vector(correction),
                            guide=GuideLine(point=c.point.copy(), direction=guide_dir),
                            constraint_dir=direction.normalized(),
                        )
                    )
        return out
