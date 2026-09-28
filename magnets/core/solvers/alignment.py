"""Alignment solver: per-axis coordinate matching for points and edges.

Each reference axis is independent. Point and edge variants share family
``alignment`` and the same per-axis snap slot.
"""

from __future__ import annotations

from mathutils import Vector

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import normalize
from ..labels import alignment_label
from ..relationship import ConstraintDelta, GuideLine, Relationship
from ..spatial import SortedProjection
from .base import BestPerKey, SolveContext, Solver


def _fallback_perp(direction: Vector) -> Vector:
    """Return a unit vector perpendicular to ``direction`` (degenerate guide)."""
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
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        # An axis snapping along the depth of an orthographic view is hidden
        # by the view filter: skip it. Per remaining axis, candidates sorted by
        # coordinate so each moving point only visits those within ``tol``.
        axes = [
            (name, direction)
            for name, direction in ctx.axes.items()
            if not ctx.direction_hidden(direction.normalized())
        ]
        indexes = [SortedProjection([c.co for c in candidates], d) for _n, d in axes]
        best = BestPerKey() if ctx.best_per_key else None
        for m in moving:
            # Same (candidate, axis) visiting order as a full nested scan.
            hits = sorted(
                (ci, ai)
                for ai, (_name, direction) in enumerate(axes)
                for ci in indexes[ai].near(m.co.dot(direction), tol)
            )
            # Candidates of one entity and kind at the same offset give the same
            # key, residual, correction and score; only their guide's anchor
            # differs, and ranking always keeps the first. Skip the rest (in
            # orthographic views, only among guides the filter treats alike).
            seen: set[tuple] = set()
            for ci, ai in hits:
                c = candidates[ci]
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                w = m.co - c.co
                axis_name, direction = axes[ai]
                along = w.dot(direction)
                residual = abs(along)
                if residual > tol:
                    continue
                # Guide line lies in the shared-coordinate plane, running from
                # the target through the (aligned) moving point: a vertical
                # guide for an X match, horizontal for Y, etc.
                perp = w - along * direction
                guide_dir = perp.normalized() if perp.length > 1e-6 else _fallback_perp(direction)
                hidden = ctx.direction_hidden(guide_dir)
                if best is not None:
                    if not hidden:  # an end-on guide is filtered out anyway
                        # id(): hashing an Enum member runs Python code.
                        key = (ai, c.entity_ref.name, id(m.kind), id(c.kind))
                        best.offer(key, residual, (m, c, axis_name, direction, along, guide_dir))
                    continue
                dup_key = (ai, c.entity_ref.name, c.kind, along, hidden)
                if dup_key in seen:
                    continue
                seen.add(dup_key)
                out.append(self._relationship(m, c, axis_name, direction, along, guide_dir, ctx))
        if best is not None:
            out = [self._relationship(*data, ctx) for data in best.winners()]
        return out

    def _relationship(self, m, c, axis_name, direction, along, guide_dir, ctx) -> Relationship:
        residual = abs(along)
        # Correction: slide the moving point along this axis until its
        # coordinate matches the candidate's. Other axes untouched.
        return Relationship(
            family=self.family,
            axis=axis_name,
            label=alignment_label(
                axis_name, c.kind, residual, ctx.unit_scale, ctx.length_format
            ),
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(-along * direction),
            guide=GuideLine(point=c.co.copy(), direction=guide_dir),
            constraint_dir=direction.normalized(),
        )


class EdgeAlignmentSolver(Solver):
    """Per-axis alignment for parallel edges.

    Unlike ``AlignmentSolver``, an axis engages only for truly parallel edges,
    not a coincidental shared coordinate.
    """

    family = "alignment"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.LINE, FeatureType.LINE)

    def solve(self, moving: list[LineFeature], candidates: list[LineFeature], ctx: SolveContext):
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        # ``lines_parallel`` normalises both directions; do each once per call.
        c_dirs = [normalize(c.direction) for c in candidates]
        for m in moving:
            m_dir = normalize(m.direction)
            m_unit = normalize(m_dir)
            for c, c_dir in zip(candidates, c_dirs):
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                if abs(abs(m_unit.dot(c_dir)) - 1.0) > 0.08:
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
