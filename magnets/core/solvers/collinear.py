"""Collinear solver: point on line."""

from __future__ import annotations

import numpy as np

from ..features import FeatureType, LineFeature, PointFeature
from ..geometry import distance_point_line, normalize, project_point_on_line
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


class CollinearSolver(Solver):
    """Point-on-line collinearity solver."""
    family = "collinear"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.LINE)

    def solve(
        self,
        moving: list[PointFeature],
        candidates: list[LineFeature],
        ctx: SolveContext,
    ):
        """Return the best relationship per rank key (see ``BestPerKey``).

        numpy screens every (moving point, line) pair; each key's winner is
        decided with the exact arithmetic (``pair_search``).
        """
        tol = ctx.world_tol
        if not moving or not candidates:
            return []
        m_co = as_array(m.co for m in moving)
        c_pt = as_array(c.point for c in candidates)
        c_dir = as_array(normalize(c.direction) for c in candidates)
        margin = coord_margin(m_co, c_pt)
        # One id table for both sides, so equal names get equal ids.
        ent = small_ids([m.entity_ref.name for m in moving] + [c.entity_ref.name for c in candidates])
        m_ent, c_ent = ent[: len(moving)], ent[len(moving):]
        m_kind = small_ids(id(m.kind) for m in moving)
        c_kind = small_ids(c.kind for c in candidates)
        n = len(candidates)

        rows_m, rows_c, rows_res, rows_corr = [], [], [], []
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            w = m_co[lo:hi, None, :] - c_pt[None, :, :]  # (b, n, 3)
            t = (w * c_dir[None]).sum(-1)
            off = t[..., None] * c_dir[None] - w  # foot of the perpendicular - m
            res = np.linalg.norm(off, axis=-1)
            ok = res <= tol + margin
            ok &= m_ent[lo:hi, None] != c_ent[None, :]
            mi, ci = np.nonzero(ok)  # C order: the original visiting order
            rows_m.append(mi + lo)
            rows_c.append(ci)
            rows_res.append(res[mi, ci])
            rows_corr.append(off[mi, ci])
        mi, ci = np.concatenate(rows_m), np.concatenate(rows_c)
        res = np.concatenate(rows_res)
        corr = np.concatenate(rows_corr).reshape(-1, 3)
        prio = np.array([m.priority for m in moving], dtype=np.float64)
        approx, walk_margin, keep = approx_rank_order(
            ctx, self.family, prio[mi], m_co[mi], corr, res, margin
        )
        mi, ci, approx = mi[keep], ci[keep], approx[keep]
        n_mk, n_ck = int(m_kind.max()) + 1, int(c_kind.max()) + 1
        group = (c_ent[ci] * n_mk + m_kind[mi]) * n_ck + c_kind[ci]
        seq = mi * n + ci

        data: dict[int, tuple] = {}
        mi_l, ci_l = mi.tolist(), ci.tolist()

        def exact(row: int):
            m, c = moving[mi_l[row]], candidates[ci_l[row]]
            residual = distance_point_line(m.co, c.point, c.direction)
            if residual > tol:
                return None
            if ctx.direction_hidden(c.direction):
                return None  # an end-on guide line is filtered out anyway
            proj = project_point_on_line(m.co, c.point, c.direction)
            ranked = exact_rank(ctx, self.family, m, residual, m.co, proj - m.co)
            if ranked is not None:
                data[row] = (m, c, residual, proj)
            return ranked

        winners = best_rows(group, approx, seq, walk_margin, exact)
        return [self._relationship(*data[row]) for row in winners]

    def _relationship(self, m, c, residual, proj) -> Relationship:
        return Relationship(
            family=self.family,
            axis=f"col_{c.entity}",
            label="-",
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(proj - m.co),
            guide=GuideLine(point=c.point.copy(), direction=c.direction.copy()),
        )
