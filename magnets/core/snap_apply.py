"""Soft-snap engage / hold / break decisions (no bpy)."""

from __future__ import annotations

HOLD = "hold"
BREAK_BAND = "break_band"
BREAK = "break"


def snap_apply_mode(
    max_screen_dist: float,
    snap_px: float,
    release_px: float,
) -> str:
    """Whether to hold, allow drag-away, or fully break a latch.

    * ``hold``: within engage tolerance; apply soft snap.
    * ``break_band``: user is dragging off the guide; do not snap back.
    * ``break``: beyond release distance; drop the latch.
    """
    if max_screen_dist > release_px:
        return BREAK
    if max_screen_dist > snap_px:
        return BREAK_BAND
    return HOLD


def masked_translation(translation, axis_mask):
    """Keep only the translation components allowed by a boolean axis mask.

    ``axis_mask`` is ``None`` (unconstrained: return the translation unchanged)
    or a 3-tuple of booleans. Used to respect a native axis/plane lock (``G X``,
    ``G Shift+Z``): the snap correction may only move along the locked axes.
    """
    if axis_mask is None:
        return type(translation)(
            (translation[0], translation[1], translation[2])
        )
    return type(translation)(
        tuple(translation[i] if axis_mask[i] else 0.0 for i in range(3))
    )


def project_out_direction(vec, normal):
    """Remove the component of ``vec`` along ``normal``.

    Args:
        vec: Input vector-like (supports indexing).
        normal: Direction to project out (need not be unit length).

    Returns:
        Vector of the same type as ``vec``, lying in the plane orthogonal to
        ``normal``. Used in orthographic views to drop the depth axis.
    """
    nx, ny, nz = normal[0], normal[1], normal[2]
    nlen = (nx * nx + ny * ny + nz * nz) ** 0.5
    if nlen < 1e-12:
        return type(vec)((vec[0], vec[1], vec[2]))
    nx, ny, nz = nx / nlen, ny / nlen, nz / nlen
    d = vec[0] * nx + vec[1] * ny + vec[2] * nz
    return type(vec)((vec[0] - d * nx, vec[1] - d * ny, vec[2] - d * nz))


def max_active_screen_dist(
    active_keys: set[tuple],
    items: list,
) -> float:
    """Largest screen distance among currently active constraint keys.

    Args:
        active_keys: Keys of engaged constraints.
        items: Rank items with screen distances.

    Returns:
        Maximum screen distance, or 0 if none.
    """
    if not active_keys or not items:
        return 0.0
    by_key: dict[tuple, float] = {}
    for it in items:
        if it.key in active_keys:
            by_key[it.key] = it.screen_dist
    if not by_key:
        return 0.0
    return max(by_key.values())
