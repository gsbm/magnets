"""Symmetry solver."""

from __future__ import annotations

import numpy as np

from ..features import FeatureType, PointFeature
from ..geometry import normalize, reflect_point
from ..pair_search import (
    approx_rank_order,
    as_array,
    best_rows,
    coord_margin,
    exact_rank,
    small_ids,
)
from ..relationship import ConstraintDelta, GuidePlane, Relationship
from .base import SolveContext, Solver

# Moving points per numpy block (bounds memory for large Edit Mode selections).
_BLOCK = 64

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
        """Return the best relationship per rank key (see ``BestPerKey``).

        numpy finds the pairs within tolerance and approximates their rank
        order; each key's winner is then decided exactly (see ``pair_search``).
        """
        tol = ctx.world_tol
        # A plane facing an orthographic view is hidden by the view filter.
        planes = [
            (plane_name, ctx.axes[axis_key], normalize(ctx.axes[axis_key]))
            for plane_name, axis_key in _SYMMETRY_PLANES
            if not ctx.direction_hidden(ctx.axes[axis_key])
        ]
        if not moving or not candidates or not planes:
            return []
        m_co = as_array(m.co for m in moving)
        c_co = as_array(c.co for c in candidates)
        units = as_array(unit for _name, _normal, unit in planes)
        margin = coord_margin(m_co, c_co)
        # One id table for both sides, so equal names get equal ids.
        ent = small_ids([m.entity_ref.name for m in moving] + [c.entity_ref.name for c in candidates])
        m_ent, c_ent = ent[: len(moving)], ent[len(moving):]
        m_kind = small_ids(id(m.kind) for m in moving)
        c_kind = small_ids(id(c.kind) for c in candidates)
        n, n_planes = len(candidates), len(planes)

        # The residual is the part of (m - c) off the plane normal.
        rows_m, rows_c, rows_p, rows_res = [], [], [], []
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            w = m_co[lo:hi, None, :] - c_co[None, :, :]
            along = w @ units.T  # (b, n, planes)
            res = np.sqrt(np.maximum((w * w).sum(-1)[:, :, None] - along * along, 0.0))
            ok = res <= tol + margin
            ok &= (m_ent[lo:hi, None] != c_ent[None, :])[:, :, None]
            mi, ci, pi = np.nonzero(ok)  # C order: the original visiting order
            rows_m.append(mi + lo)
            rows_c.append(ci)
            rows_p.append(pi)
            rows_res.append(res[mi, ci, pi])
        mi, ci, pi = (np.concatenate(r) for r in (rows_m, rows_c, rows_p))
        res = np.concatenate(rows_res)
        prio = np.array([m.priority for m in moving], dtype=np.float64)
        # The correction is the full mirror move (c - m), not the residual.
        approx, walk_margin, keep = approx_rank_order(
            ctx, self.family, prio[mi], m_co[mi], c_co[ci] - m_co[mi], res, margin
        )
        mi, ci, pi, approx = mi[keep], ci[keep], pi[keep], approx[keep]
        n_ent, n_mk, n_ck = int(c_ent.max()) + 1, int(m_kind.max()) + 1, int(c_kind.max()) + 1
        group = ((pi * n_ent + c_ent[ci]) * n_mk + m_kind[mi]) * n_ck + c_kind[ci]
        seq = (mi * n + ci) * n_planes + pi

        data: dict[int, tuple] = {}
        mi_l, ci_l, pi_l = mi.tolist(), ci.tolist(), pi.tolist()

        def exact(row: int):
            m, c = moving[mi_l[row]], candidates[ci_l[row]]
            plane_name, normal, _unit = planes[pi_l[row]]
            mid = (m.co + c.co) * 0.5
            residual = (reflect_point(m.co, mid, normal) - c.co).length
            if residual > tol:
                return None
            ranked = exact_rank(ctx, self.family, m, residual, m.co, c.co - m.co)
            if ranked is not None:
                data[row] = (m, c, plane_name, normal, residual, mid)
            return ranked

        winners = best_rows(group, approx, seq, walk_margin, exact)
        return [self._relationship(*data[row]) for row in winners]

    def _relationship(self, m, c, plane_name, normal, residual, mid) -> Relationship:
        return Relationship(
            family=self.family,
            axis=f"sym_{plane_name}_{c.entity}",
            label=f"⇹ {plane_name}",  # arrows either side of a mirror
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(c.co - m.co),
            guide=GuidePlane(point=mid.copy(), normal=normal.copy()),
        )
