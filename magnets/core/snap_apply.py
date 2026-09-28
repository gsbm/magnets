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
    """Keep only the translation components allowed by ``axis_mask``.

    ``axis_mask`` is None (unconstrained) or a 3-tuple of booleans, so a native
    axis/plane lock (``G X``, ``G Shift+Z``) is respected.
    """
    if axis_mask is None:
        return type(translation)(
            (translation[0], translation[1], translation[2])
        )
    return type(translation)(
        tuple(translation[i] if axis_mask[i] else 0.0 for i in range(3))
    )


def project_out_direction(vec, normal):
    """Remove the component of ``vec`` along ``normal`` (need not be unit).

    Returns the same type as ``vec``. Used in orthographic views to drop depth.
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
    """Return the largest screen distance among active keys, or 0.

    Each key is measured by its first item in ``items`` (best-ranked first):
    the one that engaged. Other pairs sharing the key, e.g. a far face center
    of the same object, must not break the latch.
    """
    if not active_keys or not items:
        return 0.0
    by_key: dict[tuple, float] = {}
    for it in items:
        if it.key in active_keys and it.key not in by_key:
            by_key[it.key] = it.screen_dist
    if not by_key:
        return 0.0
    return max(by_key.values())


def inferred_axis_mask(start, current, move_eps: float):
    """Global axes a native transform is visibly locked to, or None.

    Blender keeps a locked coordinate *exactly* at its start value, and the
    running operator does not report a lock typed mid-drag (``G`` then ``X``).
    So once the selection has moved more than ``move_eps``, an axis whose
    coordinate is still bit-for-bit unchanged is treated as locked. None
    before any real move, or when every axis moved (free drag).
    """
    d = [current[i] - start[i] for i in range(3)]
    if max(abs(c) for c in d) <= move_eps:
        return None
    mask = tuple(c != 0.0 for c in d)
    return None if all(mask) else mask
