"""Midpoint solver."""

from __future__ import annotations

import numpy as np

from ..features import FeatureType, PointFeature
from ..pair_search import (
    approx_rank_order,
    as_array,
    best_rows,
    coord_margin,
    entity_pairs,
    exact_rank,
    small_ids,
    straight_pairs,
)
from ..relationship import ConstraintDelta, GuideSegment, Relationship
from .base import SolveContext, Solver

# Moving points per numpy block (bounds memory for large Edit Mode selections).
_BLOCK = 64


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
        """Return the best relationship per rank key (see ``BestPerKey``).

        numpy screens every (moving point, same-kind pair) combination; each
        key's winner is decided with the exact arithmetic (``pair_search``).
        """
        tol = ctx.world_tol
        if not moving or len(candidates) < 2:
            return []
        m_co = as_array(m.co for m in moving)
        c_co = as_array(c.co for c in candidates)
        margin = coord_margin(m_co, c_co)
        # One id table for both sides, so equal names get equal ids.
        ent = small_ids([c.entity_ref.name for c in candidates] + [m.entity_ref.name for m in moving])
        c_ent, m_ent = ent[: len(candidates)], ent[len(candidates):]
        m_kind = small_ids(id(m.kind) for m in moving)
        c_kind = small_ids(id(c.kind) for c in candidates)

        # Same-kind pairs per entity, in the plain scan order.
        pa, pb = entity_pairs(c_ent)
        same = c_kind[pa] == c_kind[pb]
        pa, pb = straight_pairs(ctx, c_co, pa[same], pb[same])
        if len(pa) == 0:
            return []
        mids = (c_co[pa] + c_co[pb]) * 0.5
        n_pairs = len(pa)

        rows_m, rows_p, rows_res = [], [], []
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            res = np.linalg.norm(m_co[lo:hi, None, :] - mids[None, :, :], axis=-1)
            ok = res <= tol + margin
            ok &= m_ent[lo:hi, None] != c_ent[pa][None, :]
            mi, pi = np.nonzero(ok)  # C order: the original visiting order
            rows_m.append(mi + lo)
            rows_p.append(pi)
            rows_res.append(res[mi, pi])
        mi, pi = np.concatenate(rows_m), np.concatenate(rows_p)
        res = np.concatenate(rows_res)
        prio = np.array([m.priority for m in moving], dtype=np.float64)
        approx, walk_margin, keep = approx_rank_order(
            ctx, self.family, prio[mi], m_co[mi], mids[pi] - m_co[mi], res, margin
        )
        mi, pi, approx = mi[keep], pi[keep], approx[keep]
        n_mk, n_ck = int(m_kind.max()) + 1, int(c_kind.max()) + 1
        group = (c_ent[pa[pi]] * n_mk + m_kind[mi]) * n_ck + c_kind[pa[pi]]
        seq = mi * n_pairs + pi

        data: dict[int, tuple] = {}
        mi_l, pa_l, pb_l, pi_l = mi.tolist(), pa.tolist(), pb.tolist(), pi.tolist()

        def exact(row: int):
            m = moving[mi_l[row]]
            a, b = candidates[pa_l[pi_l[row]]], candidates[pb_l[pi_l[row]]]
            mid = (a.co + b.co) * 0.5
            residual = (m.co - mid).length
            if residual > tol:
                return None
            if ctx.direction_hidden(b.co - a.co):
                return None  # an end-on guide segment is filtered out anyway
            ranked = exact_rank(ctx, self.family, m, residual, m.co, mid - m.co)
            if ranked is not None:
                data[row] = (m, a, b, residual, mid)
            return ranked

        winners = best_rows(group, approx, seq, walk_margin, exact)
        return [self._relationship(*data[row]) for row in winners]

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
