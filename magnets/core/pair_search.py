"""Vectorised pair search with exact per-key winners (numpy; no bpy).

Solvers score every (moving, candidate) pair at once with numpy in double
precision, then decide each rank key's winner with their original
(single-precision mathutils) arithmetic. numpy only picks which pairs are
worth that exact look: pairs are ordered by an approximate value, and a key's
walk stops once the next approximation is beyond the best exact value plus a
margin that bounds the difference between the two. The winners are therefore
exactly those of a full scan.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable

import numpy as np

from .scoring import FAMILY_PRIORITY

# float32 rounding is ~1.2e-7 relative; margins use ~20x that per unit scale.
_REL_MARGIN = 1e-5


def as_array(vectors: Iterable) -> np.ndarray:
    """``(n, 3)`` float64 array of 3D vectors."""
    out = np.array([tuple(v) for v in vectors], dtype=np.float64)
    return out.reshape(-1, 3)


def small_ids(values: Iterable[Hashable]) -> np.ndarray:
    """Map hashable values to consecutive small ints (equal values, equal ids)."""
    table: dict = {}
    return np.array([table.setdefault(v, len(table)) for v in values], dtype=np.int64)


def coord_margin(*arrays: np.ndarray) -> float:
    """Margin covering single-precision error for coordinates of this scale."""
    scale = 1.0
    for arr in arrays:
        if arr.size:
            scale = max(scale, float(np.abs(arr).max()))
    return _REL_MARGIN * scale


def entity_pairs(entity_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Index pairs ``(i, j)``, i before j, of candidates sharing an entity.

    ``entity_ids`` come from ``small_ids`` (numbered by first appearance), so
    pairs follow the plain scan order: entities by first appearance, then
    each entity's points in candidate order, i outer and j inner.
    """
    firsts, seconds = [], []
    for e in range(int(entity_ids.max()) + 1 if len(entity_ids) else 0):
        idx = np.flatnonzero(entity_ids == e)
        i, j = np.triu_indices(len(idx), 1)
        firsts.append(idx[i])
        seconds.append(idx[j])
    if not firsts:
        empty = np.zeros(0, dtype=np.int64)
        return empty, empty
    return np.concatenate(firsts), np.concatenate(seconds)


def project_px(projection, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Approximate ``location_3d_to_region_2d`` for many points.

    ``projection`` is ``(4x4 perspective matrix rows, width, height)``.
    Returns ``(xy, valid)``; invalid rows are behind the viewer.
    """
    matrix, width, height = projection
    m = np.asarray(matrix, dtype=np.float64)
    homo = np.hstack([points, np.ones((len(points), 1))])
    prj = homo @ m.T
    w = prj[:, 3]
    valid = w > 0.0
    safe_w = np.where(valid, w, 1.0)
    half = np.array([width / 2.0, height / 2.0])
    xy = half + half * (prj[:, :2] / safe_w[:, None])
    return xy, valid


def approx_rank_order(
    ctx,
    family: str,
    priority: np.ndarray,
    moving_co: np.ndarray,
    correction: np.ndarray,
    residual: np.ndarray,
    margin: float,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Approximate ``SolveContext.rank_order`` per row: ``(approx, walk margin, keep)``.

    ``priority``, ``moving_co``, ``correction`` and ``residual`` are per row;
    ``margin`` bounds the world-space error of the inputs. Without a
    projection the order is the residual. With one it is -score from the
    approximate screen distance; rows clearly beyond the passive range are
    dropped (``keep``) and off-screen rows sort first, so they are decided
    exactly.
    """
    if ctx.projection is None or ctx.screen_dist is None:
        return residual, margin, np.ones(len(residual), dtype=bool)
    _matrix, width, height = ctx.projection
    margin_px = 1e-4 * (width + height)
    a_xy, a_ok = project_px(ctx.projection, moving_co)
    b_xy, b_ok = project_px(ctx.projection, moving_co + correction)
    sd = np.linalg.norm(b_xy - a_xy, axis=1)
    valid = a_ok & b_ok
    keep = ~valid | (sd <= ctx.passive_px + margin_px)
    passive = max(ctx.passive_px, 1.0)
    tol = max(ctx.world_tol, 1e-9)
    score = (
        FAMILY_PRIORITY.get(family, 0) * 1000.0
        + priority * 10.0
        + np.maximum(0.0, 1.0 - sd / passive) * 100.0
        + np.maximum(0.0, 1.0 - residual / tol) * 50.0
        - sd
    )
    approx = np.where(valid, -score, -np.inf)
    walk_margin = margin_px * (1.0 + 100.0 / passive) + 50.0 * margin / tol + 1e-6
    return approx, walk_margin, keep


def exact_rank(ctx, family: str, moving, residual: float, moving_co, correction):
    """``(scalar, order)`` for ``best_rows`` from ``ctx.rank_order``, or None."""
    order = ctx.rank_order(family, moving, residual, moving_co, correction)
    if order is None:
        return None
    return order[0], order


def best_rows(
    group: np.ndarray,
    approx: np.ndarray,
    seq: np.ndarray,
    margin: float,
    exact: Callable[[int], tuple[float, tuple] | None],
) -> list[int]:
    """Rows that win their group under ``exact``, in ``seq`` order.

    ``exact(row)`` returns ``(scalar, order)`` or None (the row does not
    count): ``order`` is the full comparison key (lower wins, then lower
    ``seq``) and ``scalar`` its leading value, within ``margin / 2`` of
    ``approx[row]``. Rows are visited per group in approximate order and a
    group's walk stops once ``approx`` exceeds the best ``scalar`` + ``margin``.
    """
    if len(group) == 0:
        return []
    order_idx = np.lexsort((seq, approx, group))
    g = group[order_idx]
    starts = np.flatnonzero(np.r_[True, g[1:] != g[:-1]]).tolist()
    ends = starts[1:] + [len(order_idx)]
    rows = order_idx.tolist()
    approx_l = approx[order_idx].tolist()
    seq_l = seq.tolist()
    winners: list[int] = []
    for start, end in zip(starts, ends):
        best_key = None
        best_scalar = 0.0
        best_row = -1
        for p in range(start, end):
            if best_key is not None and approx_l[p] > best_scalar + margin:
                break
            row = rows[p]
            result = exact(row)
            if result is None:
                continue
            scalar, order = result
            key = (order, seq_l[row])
            if best_key is None or key < best_key:
                best_key, best_scalar, best_row = key, scalar, row
        if best_key is not None:
            winners.append(best_row)
    winners.sort(key=seq_l.__getitem__)
    return winners
