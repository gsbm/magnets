"""Repeat Size solver: repeat a candidate object's own span as a gap."""

from __future__ import annotations

from functools import partial

import numpy as np

from ..features import FeatureType, PointFeature
from ..geometry import collinear
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


def _gap_label(ctx: SolveContext, ab: float) -> str:
    return ctx.format_length(ab)


class SpacingSolver(Solver):
    """Repeat Size: place the selection one span of an object away from it.

    Equal spacing *between* objects is ``DistributionSolver``.
    """
    family = "repeat_size"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        return (FeatureType.POINT, FeatureType.POINT)

    def solve(self, moving: list[PointFeature], candidates: list[PointFeature], ctx: SolveContext):
        """Return the best relationship per rank key (see ``pair_search``).

        For each pair of points (a, b) of one candidate entity, the moving
        point on their line at distance |ab| from a or b repeats that gap.
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

        pa, pb = straight_pairs(ctx, c_co, *entity_pairs(c_ent))
        a_co, b_co = c_co[pa], c_co[pb]
        ab_vec = b_co - a_co
        ab = np.linalg.norm(ab_vec, axis=1)
        live = ab > ctx.min_gap - margin
        pa, pb, a_co, b_co, ab_vec, ab = pa[live], pb[live], a_co[live], b_co[live], ab_vec[live], ab[live]
        if len(pa) == 0:
            return []
        unit = ab_vec / ab[:, None]
        n_pairs = len(pa)

        rows = {k: [] for k in ("m", "p", "t", "res", "corr")}
        for lo in range(0, len(moving), _BLOCK):
            hi = min(lo + _BLOCK, len(moving))
            ma = m_co[lo:hi, None, :] - a_co[None, :, :]  # (b, pairs, 3)
            along = (ma * unit[None]).sum(-1)
            perp = np.linalg.norm(ma - along[..., None] * unit[None], axis=-1)
            on_line = perp <= tol + margin
            on_line &= m_ent[lo:hi, None] != c_ent[pa][None, :]
            gap_a = np.linalg.norm(ma, axis=-1)
            gap_b = np.linalg.norm(m_co[lo:hi, None, :] - b_co[None, :, :], axis=-1)
            res = np.stack([np.abs(gap_a - ab), np.abs(gap_b - ab)], axis=-1)  # (b, pairs, 2)
            ok = on_line[..., None] & (res <= tol + margin)
            mi, pi, ti = np.nonzero(ok)  # C order: the original visiting order
            # Same target spot for either end: a + |ab| along ab, else b back.
            m_rows = m_co[mi + lo]
            desired = a_co[pi] + unit[pi] * ab[pi, None]
            far = np.linalg.norm(desired - m_rows, axis=1) > 2.0 * ab[pi]
            desired[far] = b_co[pi][far] - unit[pi][far] * ab[pi][far, None]
            rows["m"].append(mi + lo)
            rows["p"].append(pi)
            rows["t"].append(ti)
            rows["res"].append(res[mi, pi, ti])
            rows["corr"].append(desired - m_rows)
        mi, pi, ti = (np.concatenate(rows[k]) for k in ("m", "p", "t"))
        res = np.concatenate(rows["res"])
        corr = np.concatenate(rows["corr"]).reshape(-1, 3)
        prio = np.array([m.priority for m in moving], dtype=np.float64)
        approx, walk_margin, keep = approx_rank_order(
            ctx, self.family, prio[mi], m_co[mi], corr, res, margin
        )
        mi, pi, ti, approx = mi[keep], pi[keep], ti[keep], approx[keep]
        n_mk, n_ck = int(m_kind.max()) + 1, int(c_kind.max()) + 1
        group = (c_ent[pa[pi]] * n_mk + m_kind[mi]) * n_ck + c_kind[pa[pi]]
        seq = (mi * n_pairs + pi) * 2 + ti

        data: dict[int, tuple] = {}
        mi_l, pa_l, pb_l, pi_l, ti_l = mi.tolist(), pa.tolist(), pb.tolist(), pi.tolist(), ti.tolist()

        def exact(row: int):
            m = moving[mi_l[row]]
            a, b = candidates[pa_l[pi_l[row]]], candidates[pb_l[pi_l[row]]]
            ab_len = (b.co - a.co).length
            if ab_len <= ctx.min_gap or not collinear(a.co, b.co, m.co, tol):
                return None
            if ctx.direction_hidden(b.co - a.co):
                return None  # an end-on guide segment is filtered out anyway
            target = a if ti_l[row] == 0 else b
            residual = abs((m.co - target.co).length - ab_len)
            if residual > tol:
                return None
            desired = a.co + (b.co - a.co).normalized() * ab_len
            if (desired - m.co).length > ab_len * 2:
                desired = b.co + (a.co - b.co).normalized() * ab_len
            delta = desired - m.co
            ranked = exact_rank(ctx, self.family, m, residual, m.co, delta)
            if ranked is not None:
                data[row] = (m, a, b, target, residual, delta, ab_len)
            return ranked

        winners = best_rows(group, approx, seq, walk_margin, exact)
        return [self._relationship(*data[row], ctx) for row in winners]

    def _relationship(self, m, a, b, target, residual, delta, ab_len, ctx) -> Relationship:
        return Relationship(
            family=self.family,
            axis=f"gap_{target.entity}",
            label=partial(_gap_label, ctx, ab_len),
            moving=m,
            targets=(a, b),
            residual=residual,
            delta=ConstraintDelta.from_vector(delta),
            guide=GuideSegment(a=a.co.copy(), b=b.co.copy()),
        )
