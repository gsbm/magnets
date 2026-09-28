"""View culling and per-object feature level of detail (numpy; no bpy).

The Illustrator smart-guides model, applied to 3D candidates:

* an object whose screen rectangle is off-screen offers no guides;
* the few objects closest to the moving selection on screen, and its nearest
  neighbours in the same screen row or column ("near"), offer every feature
  to every solver;
* every other on-screen object ("far") offers only its min / centre / max on
  each axis (centroid, bbox face centres, origin), only to alignment, and
  only within the snap release band (Illustrator shows no guide until it
  snaps; the passive band stays for near objects).

Screen rectangles come from each object's point features projected through
the view's perspective matrix. They are computed once per view, not per tick:
a native drag rarely changes the view, and the key detects when it does.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .features import FeaturePool, PointFeature, PointKind

# Point kinds a far object still offers. Between them they carry the min,
# centre and max of the bbox on every axis, which is all per-axis alignment
# reads; corners, edges and planes repeat those coordinates or need pairs.
FAR_POINT_KINDS = frozenset(
    (PointKind.CENTROID, PointKind.BBOX_FACE_CENTER, PointKind.ORIGIN)
)
# Families that still run against far objects.
FAR_FAMILIES = frozenset(("alignment",))


def far_moving(moving: FeaturePool) -> FeaturePool:
    """The moving points matched against far objects: its min / centre / max.

    Falls back to every moving point when none has a far kind (Edit Mode
    vertices, for instance).
    """
    points = [p for p in moving.points if p.kind in FAR_POINT_KINDS]
    return FeaturePool(points=points or list(moving.points))


def project_points(co: np.ndarray, projection) -> tuple[np.ndarray, np.ndarray]:
    """Project ``(n, 3)`` world points to region pixels.

    ``projection`` is ``(perspective_matrix_rows, width, height)``, as in
    ``SolveContext.projection``. Returns ``(xy, in_front)``; ``xy`` rows for
    points behind the viewer (``w <= 0``) are meaningless. Same maths as
    ``view3d_utils.location_3d_to_region_2d``.
    """
    rows, width, height = projection
    mat = np.asarray(rows, dtype=np.float64)
    hom = co @ mat[:, :3].T + mat[:, 3]
    w = hom[:, 3]
    in_front = w > 0.0
    safe_w = np.where(in_front, w, 1.0)
    xy = np.empty((len(co), 2), dtype=np.float64)
    xy[:, 0] = (width / 2.0) * (1.0 + hom[:, 0] / safe_w)
    xy[:, 1] = (height / 2.0) * (1.0 + hom[:, 1] / safe_w)
    return xy, in_front


def rect_distance(rects: np.ndarray, rect) -> np.ndarray:
    """Screen distance from each ``(xmin, ymin, xmax, ymax)`` row to ``rect``."""
    dx = np.maximum(0.0, np.maximum(rects[:, 0] - rect[2], rect[0] - rects[:, 2]))
    dy = np.maximum(0.0, np.maximum(rects[:, 1] - rect[3], rect[1] - rects[:, 3]))
    return np.hypot(dx, dy)


@dataclass
class ViewTiers:
    """Per-tick object classification (entity names)."""

    near: frozenset
    far: frozenset


class ViewLOD:
    """Screen rectangles of the candidate objects, cached per view."""

    def __init__(self, pool: FeaturePool):
        names = [p.entity for p in pool.points]
        order = sorted(range(len(names)), key=names.__getitem__)
        self._co = (
            np.array([tuple(pool.points[i].co) for i in order], dtype=np.float64).reshape(-1, 3)
        )
        sorted_names = [names[i] for i in order]
        starts = [i for i in range(len(sorted_names)) if i == 0 or sorted_names[i] != sorted_names[i - 1]]
        self._starts = np.array(starts, dtype=np.int64)
        self.entities = [sorted_names[i] for i in starts]
        # Objects with features but no points: never culled, always near.
        with_points = set(self.entities)
        self._pointless = frozenset(
            f.entity for f in _non_point_features(pool) if f.entity not in with_points
        )
        # Features per object, for building the tier pools without a scan.
        self._by_entity: dict[str, list] = {}
        for _anchor, feat in pool.anchor_items():
            self._by_entity.setdefault(feat.entity, []).append(feat)
        self._far_cache: tuple | None = None
        self._view_key = None
        self._rects = np.zeros((0, 4))
        self._straddles = np.zeros(0, dtype=bool)
        self._behind = np.zeros(0, dtype=bool)

    def _update_view(self, projection) -> None:
        key = (tuple(map(tuple, projection[0])), projection[1], projection[2])
        if key == self._view_key:
            return
        self._view_key = key
        if not len(self._starts):
            return
        xy, in_front = project_points(self._co, projection)
        starts = self._starts
        self._rects = np.stack(
            [
                np.minimum.reduceat(xy[:, 0], starts),
                np.minimum.reduceat(xy[:, 1], starts),
                np.maximum.reduceat(xy[:, 0], starts),
                np.maximum.reduceat(xy[:, 1], starts),
            ],
            axis=1,
        )
        # Partly behind the viewer: the rectangle is unreliable, keep it near.
        self._straddles = np.logical_and.reduceat(in_front, starts) == 0
        self._behind = np.logical_or.reduceat(in_front, starts) == 0

    def tiers(
        self,
        projection,
        moving_co: np.ndarray,
        *,
        margin_px: float,
        max_near: int,
        row_neighbours: int = 2,
    ) -> ViewTiers:
        """Classify every candidate object for this tick.

        ``moving_co`` are the moving selection's world points; "near" is
        measured from their screen rectangle. Near objects are the
        ``max_near`` closest on-screen objects, plus the ``row_neighbours``
        closest on each side that share the selection's screen row or column
        (Illustrator's equal-spacing neighbours), plus objects straddling the
        viewer or without points. ``margin_px`` widens the region for the
        on-screen test. Every other on-screen object is far.
        """
        self._update_view(projection)
        if not self.entities:
            return ViewTiers(near=self._pointless, far=frozenset())
        _rows, width, height = projection
        rects = self._rects
        straddles = self._straddles & ~self._behind
        on_screen = (
            (rects[:, 2] >= -margin_px)
            & (rects[:, 0] <= width + margin_px)
            & (rects[:, 3] >= -margin_px)
            & (rects[:, 1] <= height + margin_px)
            & ~self._behind
        ) | straddles

        near = straddles.copy()
        if len(moving_co):
            m_xy, m_front = project_points(np.asarray(moving_co, dtype=np.float64).reshape(-1, 3), projection)
            if m_front.any():
                m_xy = m_xy[m_front]
                m = (m_xy[:, 0].min(), m_xy[:, 1].min(), m_xy[:, 0].max(), m_xy[:, 1].max())
                usable = on_screen & ~straddles
                _pick_closest(near, usable, rect_distance(rects, m), max_near)
                if row_neighbours > 0:
                    row = usable & (rects[:, 1] <= m[3]) & (rects[:, 3] >= m[1])
                    col = usable & (rects[:, 0] <= m[2]) & (rects[:, 2] >= m[0])
                    for side, gap in (
                        (row, m[0] - rects[:, 2]),  # left
                        (row, rects[:, 0] - m[2]),  # right
                        (col, m[1] - rects[:, 3]),  # below
                        (col, rects[:, 1] - m[3]),  # above
                    ):
                        _pick_closest(near, side & (gap >= 0.0), gap, row_neighbours)

        names = self.entities
        near_set = frozenset(names[i] for i in np.nonzero(near)[0]) | self._pointless
        far_set = frozenset(names[i] for i in np.nonzero(on_screen & ~near)[0])
        return ViewTiers(near=near_set, far=far_set)


    def pools(self, tiers: ViewTiers, families: set[str]) -> tuple[FeaturePool, FeaturePool]:
        """Return ``(near_pool, far_pool)`` for ``tiers``.

        The near pool holds every feature of the near objects and is fresh
        each call (callers may append to it). The far pool holds only
        ``FAR_POINT_KINDS`` points, is empty when no far family is enabled,
        and is shared between calls with the same far set: do not mutate it.
        """
        by_entity = self._by_entity
        near_feats = [f for ent in sorted(tiers.near) for f in by_entity.get(ent, ())]
        want_far = bool(families & FAR_FAMILIES)
        key = (tiers.far, want_far)
        if self._far_cache is None or self._far_cache[0] != key:
            far_feats = []
            if want_far:
                for ent in sorted(tiers.far):
                    far_feats.extend(
                        f
                        for f in by_entity.get(ent, ())
                        if isinstance(f, PointFeature) and f.kind in FAR_POINT_KINDS
                    )
            self._far_cache = (key, FeaturePool.from_features(far_feats))
        return FeaturePool.from_features(near_feats), self._far_cache[1]


def _pick_closest(out: np.ndarray, mask: np.ndarray, dist: np.ndarray, k: int) -> None:
    """Set ``out`` for the ``k`` rows of ``mask`` with the smallest ``dist``."""
    idx = np.nonzero(mask)[0]
    if len(idx) > k:
        idx = idx[np.argsort(dist[idx], kind="stable")[:k]]
    out[idx] = True


def _non_point_features(pool: FeaturePool):
    for group in (pool.lines, pool.planes, pool.directions, pool.bboxes, pool.circles, pool.surfaces):
        yield from group
