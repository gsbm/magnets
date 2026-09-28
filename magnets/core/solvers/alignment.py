"""Alignment solver: per-axis coordinate matching for points and edges.

Each reference axis is independent. Point and edge variants share family
``alignment`` and the same per-axis snap slot.
"""

from __future__ import annotations

import numpy as np
from mathutils import Vector

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import normalize
from ..labels import alignment_label
from ..pair_search import as_array, best_rows, coord_margin, small_ids
from ..relationship import ConstraintDelta, GuideLine, Relationship
from .base import SolveContext, Solver

# Moving points per numpy block (bounds memory for large Edit Mode selections).
_BLOCK = 64


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
        """Return the best relationship per rank key (see ``BestPerKey``).

        numpy finds the pairs within tolerance; each key's winner is then
        decided with the exact per-pair arithmetic (see ``pair_search``).
        """
        tol = ctx.world_tol
        # An axis snapping along the depth of an orthographic view is hidden
        # by the view filter: skip it.
        axes = [
            (name, direction)
            for name, direction in ctx.axes.items()
            if not ctx.direction_hidden(direction.normalized())
        ]
        if not moving or not candidates or not axes:
            return []
        m_co = as_array(m.co for m in moving)
        c_co = as_array(c.co for c in candidates)
        dirs = as_array(d for _n, d in axes)
        margin = coord_margin(m_co, c_co)
        # One id table for both sides, so equal names get equal ids.
        ent = small_ids([m.entity_ref.name for m in moving] + [c.entity_ref.name for c in candidates])
        m_ent, c_ent = ent[: len(moving)], ent[len(moving):]
        m_kind = small_ids(id(m.kind) for m in moving)
        c_kind = small_ids(id(c.kind) for c in candidates)
        n, n_axes = len(candidates), len(axes)

        rows_m, rows_c, rows_a, rows_res = [], [], [], []
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            along = (m_co[lo:hi, None, :] - c_co[None, :, :]) @ dirs.T  # (b, n, axes)
            ok = np.abs(along) <= tol + margin
            ok &= (m_ent[lo:hi, None] != c_ent[None, :])[:, :, None]
            mi, ci, ai = np.nonzero(ok)  # C order: the original visiting order
            rows_m.append(mi + lo)
            rows_c.append(ci)
            rows_a.append(ai)
            rows_res.append(np.abs(along[mi, ci, ai]))
        mi, ci, ai = (np.concatenate(r) for r in (rows_m, rows_c, rows_a))
        approx = np.concatenate(rows_res)
        n_ent, n_mk, n_ck = int(c_ent.max()) + 1, int(m_kind.max()) + 1, int(c_kind.max()) + 1
        group = ((ai * n_ent + c_ent[ci]) * n_mk + m_kind[mi]) * n_ck + c_kind[ci]
        seq = (mi * n + ci) * n_axes + ai

        data: dict[int, tuple] = {}
        mi_l, ci_l, ai_l = mi.tolist(), ci.tolist(), ai.tolist()

        def exact(row: int):
            m, c = moving[mi_l[row]], candidates[ci_l[row]]
            axis_name, direction = axes[ai_l[row]]
            w = m.co - c.co
            along = w.dot(direction)
            residual = abs(along)
            if residual > tol:
                return None
            # Guide line lies in the shared-coordinate plane, running from the
            # target through the (aligned) moving point: a vertical guide for
            # an X match, horizontal for Y, etc.
            perp = w - along * direction
            guide_dir = perp.normalized() if perp.length > 1e-6 else _fallback_perp(direction)
            if ctx.direction_hidden(guide_dir):
                return None  # an end-on guide is filtered out anyway
            data[row] = (m, c, axis_name, direction, along, guide_dir)
            return residual, (residual,)

        winners = best_rows(group, approx, seq, margin, exact)
        return [self._relationship(*data[row], ctx) for row in winners]

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
