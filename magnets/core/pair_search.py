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
