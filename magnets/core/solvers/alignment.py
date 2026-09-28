"""Alignment solver: per-axis coordinate matching for points and edges.

Each reference axis is independent. Point and edge variants share family
``alignment`` and the same per-axis snap slot.
"""

from __future__ import annotations

from functools import partial

import numpy as np
from mathutils import Vector

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import normalize
from ..labels import alignment_label
from ..pair_search import (
    approx_rank_order,
    as_array,
    best_rows,
    coord_margin,
    exact_rank,
    small_ids,
)
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

        rows_m, rows_c, rows_a, rows_along = [], [], [], []
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            along = (m_co[lo:hi, None, :] - c_co[None, :, :]) @ dirs.T  # (b, n, axes)
            ok = np.abs(along) <= tol + margin
            ok &= (m_ent[lo:hi, None] != c_ent[None, :])[:, :, None]
            mi, ci, ai = np.nonzero(ok)  # C order: the original visiting order
            rows_m.append(mi + lo)
            rows_c.append(ci)
            rows_a.append(ai)
            rows_along.append(along[mi, ci, ai])
        mi, ci, ai = (np.concatenate(r) for r in (rows_m, rows_c, rows_a))
        along = np.concatenate(rows_along)
        prio = np.array([m.priority for m in moving], dtype=np.float64)
        approx, walk_margin, keep = approx_rank_order(
            ctx, self.family, prio[mi], m_co[mi], -along[:, None] * dirs[ai], np.abs(along), margin
        )
        mi, ci, ai, approx = mi[keep], ci[keep], ai[keep], approx[keep]
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
            ranked = exact_rank(ctx, self.family, m, residual, m.co, -along * direction)
            if ranked is not None:
                data[row] = (m, c, axis_name, direction, along, guide_dir)
            return ranked

        winners = best_rows(group, approx, seq, walk_margin, exact)
        return [self._relationship(*data[row], ctx) for row in winners]

    def _relationship(self, m, c, axis_name, direction, along, guide_dir, ctx) -> Relationship:
        residual = abs(along)
        # Correction: slide the moving point along this axis until its
        # coordinate matches the candidate's. Other axes untouched.
        return Relationship(
            family=self.family,
            axis=axis_name,
            # Formatted only if the guide is drawn (see Relationship.label).
            label=partial(
                alignment_label, axis_name, c.kind, residual, ctx.unit_scale, ctx.length_format
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
        """Return the best relationship per rank key (see ``BestPerKey``).

        numpy screens every (moving edge, candidate edge, axis) triple; each
        key's winner is decided with the exact arithmetic (``pair_search``).
        """
        tol = ctx.world_tol
        axes = list(ctx.axes.items())
        if not moving or not candidates or not axes:
            return []
        m_pt = as_array(m.point for m in moving)
        c_pt = as_array(c.point for c in candidates)
        m_dir = as_array(normalize(m.direction) for m in moving)
        c_dir = as_array(normalize(c.direction) for c in candidates)
        dirs = as_array(d for _n, d in axes)
        margin = coord_margin(m_pt, c_pt)
        # One id table for both sides, so equal names get equal ids.
        ent = small_ids([m.entity_ref.name for m in moving] + [c.entity_ref.name for c in candidates])
        m_ent, c_ent = ent[: len(moving)], ent[len(moving):]
        m_kind = small_ids(m.kind for m in moving)
        c_kind = small_ids(c.kind for c in candidates)
        n, n_axes = len(candidates), len(axes)

        # Parallel edges (|cos| near 1) and axes the edge does not run along;
        # small slack at both cutoffs, which the exact test settles.
        across = np.abs(m_dir @ dirs.T) <= 0.9 + 1e-5  # (k, axes)
        rows_m, rows_c, rows_a, rows_along = [], [], [], []
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            parallel = np.abs(np.abs(m_dir[lo:hi] @ c_dir.T) - 1.0) <= 0.08 + 1e-5
            parallel &= m_ent[lo:hi, None] != c_ent[None, :]
            along = (m_pt[lo:hi, None, :] - c_pt[None, :, :]) @ dirs.T  # (b, n, axes)
            ok = parallel[:, :, None] & across[lo:hi, None, :] & (np.abs(along) <= tol + margin)
            mi, ci, ai = np.nonzero(ok)  # C order: the original visiting order
            rows_m.append(mi + lo)
            rows_c.append(ci)
            rows_a.append(ai)
            rows_along.append(along[mi, ci, ai])
        mi, ci, ai = (np.concatenate(r) for r in (rows_m, rows_c, rows_a))
        along = np.concatenate(rows_along)
        prio = np.array([m.priority for m in moving], dtype=np.float64)
        approx, walk_margin, keep = approx_rank_order(
            ctx, self.family, prio[mi], m_pt[mi], -along[:, None] * dirs[ai], np.abs(along), margin
        )
        mi, ci, ai, approx = mi[keep], ci[keep], ai[keep], approx[keep]
        n_ent, n_mk, n_ck = int(ent.max()) + 1, int(m_kind.max()) + 1, int(c_kind.max()) + 1
        group = ((ai * n_ent + c_ent[ci]) * n_mk + m_kind[mi]) * n_ck + c_kind[ci]
        seq = (mi * n + ci) * n_axes + ai

        data: dict[int, tuple] = {}
        mi_l, ci_l, ai_l = mi.tolist(), ci.tolist(), ai.tolist()

        def exact(row: int):
            m, c = moving[mi_l[row]], candidates[ci_l[row]]
            m_dir = normalize(m.direction)
            # Same arithmetic as ``lines_parallel(m_dir, c.direction)``.
            if abs(abs(normalize(m_dir).dot(normalize(c.direction))) - 1.0) > 0.08:
                return None
            axis_name, direction = axes[ai_l[row]]
            # An infinite line has no meaningful offset along its own
            # direction: skip axes the edge runs parallel to.
            if abs(m_dir.dot(direction)) > 0.9:
                return None
            w = m.point - c.point
            along = w.dot(direction)
            residual = abs(along)
            if residual > tol:
                return None
            perp = w - along * direction
            guide_dir = perp.normalized() if perp.length > 1e-6 else _fallback_perp(direction)
            if ctx.direction_hidden(direction.normalized()) or ctx.direction_hidden(guide_dir):
                return None  # the view filter drops these anyway
            ranked = exact_rank(ctx, self.family, m, residual, m.point, -along * direction)
            if ranked is not None:
                data[row] = (m, c, axis_name, direction, along, residual, guide_dir)
            return ranked

        winners = best_rows(group, approx, seq, walk_margin, exact)
        return [self._relationship(*data[row], ctx) for row in winners]

    def _relationship(self, m, c, axis_name, direction, along, residual, guide_dir, ctx):
        return Relationship(
            family=self.family,
            axis=axis_name,
            # Formatted only if the guide is drawn (see Relationship.label).
            label=partial(
                alignment_label, axis_name, c.kind, residual, ctx.unit_scale, ctx.length_format
            ),
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(-along * direction),
            guide=GuideLine(point=c.point.copy(), direction=guide_dir),
            constraint_dir=direction.normalized(),
        )
