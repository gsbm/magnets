"""Spatial indexes for broad-phase candidate queries.

Provides KDTree (default), uniform hash grid, and a BVH placeholder. All share
the same query interface so the pipeline can swap strategies without touching
callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mathutils import Vector

try:  # pragma: no cover - exercised by whichever backend is present
    from mathutils.kdtree import KDTree

    _HAVE_KDTREE = True
except Exception:  # pragma: no cover
    _HAVE_KDTREE = False


class SpatialIndex(ABC):
    """Broad-phase index over ``(co, payload)`` pairs."""

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def query_radius(self, center: Vector, radius: float) -> list:
        """Return payloads within ``radius`` of ``center``.

        Args:
            center: Query origin.
            radius: Search radius.

        Returns:
            Matching payloads.
        """
        ...

    @abstractmethod
    def query_nearest(self, center: Vector, n: int) -> list:
        """Return up to ``n`` nearest payloads to ``center``.

        Args:
            center: Query origin.
            n: Maximum results.

        Returns:
            Nearest payloads.
        """
        ...


class PointIndex(SpatialIndex):
    """KDTree-backed index (brute-force fallback when kdtree is unavailable)."""

    def __init__(self, items: list[tuple[Vector, object]]):
        self._items = list(items)
        self._tree = None
        if _HAVE_KDTREE and self._items:
            tree = KDTree(len(self._items))
            for i, (co, _payload) in enumerate(self._items):
                tree.insert(co, i)
            tree.balance()
            self._tree = tree

    def __len__(self) -> int:
        return len(self._items)

    def query_radius(self, center: Vector, radius: float) -> list:
        """Return payloads within ``radius`` of ``center``.

        Args:
            center: Query origin.
            radius: Search radius.

        Returns:
            Matching payloads.
        """
        if self._tree is not None:
            return [self._items[i][1] for (_co, i, _d) in self._tree.find_range(center, radius)]
        r2 = radius * radius
        return [p for (co, p) in self._items if (co - center).length_squared <= r2]

    def query_nearest(self, center: Vector, n: int) -> list:
        """Return up to ``n`` nearest payloads to ``center``.

        Args:
            center: Query origin.
            n: Maximum results.

        Returns:
            Nearest payloads.
        """
        if n <= 0 or not self._items:
            return []
        if self._tree is not None:
            return [self._items[i][1] for (_co, i, _d) in self._tree.find_n(center, n)]
        ordered = sorted(self._items, key=lambda it: (it[0] - center).length_squared)
        return [p for (_co, p) in ordered[:n]]


class HashGridIndex(SpatialIndex):
    """Uniform spatial hash — fast for locally dense point clouds."""

    def __init__(self, items: list[tuple[Vector, object]], cell_size: float):
        self._cell_size = max(cell_size, 1e-6)
        self._items = list(items)
        self._grid: dict[tuple[int, int, int], list[tuple[Vector, object]]] = {}
        for co, payload in self._items:
            self._grid.setdefault(self._cell_key(co), []).append((co, payload))

    def _cell_key(self, co: Vector) -> tuple[int, int, int]:
        cs = self._cell_size
        return (int(co.x / cs), int(co.y / cs), int(co.z / cs))

    def __len__(self) -> int:
        return len(self._items)

    def query_radius(self, center: Vector, radius: float) -> list:
        """Return payloads within ``radius`` of ``center``.

        Args:
            center: Query origin.
            radius: Search radius.

        Returns:
            Matching payloads.
        """
        r2 = radius * radius
        cells = int(radius / self._cell_size) + 1
        cx, cy, cz = self._cell_key(center)
        out: list = []
        seen: set[int] = set()
        for dx in range(-cells, cells + 1):
            for dy in range(-cells, cells + 1):
                for dz in range(-cells, cells + 1):
                    for co, payload in self._grid.get((cx + dx, cy + dy, cz + dz), []):
                        pid = id(payload)
                        if pid in seen:
                            continue
                        if (co - center).length_squared <= r2:
                            seen.add(pid)
                            out.append(payload)
        return out

    def query_nearest(self, center: Vector, n: int) -> list:
        """Return up to ``n`` nearest payloads to ``center``.

        Args:
            center: Query origin.
            n: Maximum results.

        Returns:
            Nearest payloads.
        """
        if n <= 0 or not self._items:
            return []
        ordered = sorted(self._items, key=lambda it: (it[0] - center).length_squared)
        return [p for (_co, p) in ordered[:n]]


class BVHIndex(SpatialIndex):
    """Placeholder for mesh/surface broad phase (Phase 6 tangency).

    Currently delegates to brute-force point queries over injected items.
    """

    def __init__(self, items: list[tuple[Vector, object]]):
        self._items = list(items)

    def __len__(self) -> int:
        return len(self._items)

    def query_radius(self, center: Vector, radius: float) -> list:
        """Return payloads within ``radius`` of ``center``.

        Args:
            center: Query origin.
            radius: Search radius.

        Returns:
            Matching payloads.
        """
        r2 = radius * radius
        return [p for (co, p) in self._items if (co - center).length_squared <= r2]

    def query_nearest(self, center: Vector, n: int) -> list:
        """Return up to ``n`` nearest payloads to ``center``.

        Args:
            center: Query origin.
            n: Maximum results.

        Returns:
            Nearest payloads.
        """
        if n <= 0 or not self._items:
            return []
        ordered = sorted(self._items, key=lambda it: (it[0] - center).length_squared)
        return [p for (_co, p) in ordered[:n]]


def build_point_index(
    items: list[tuple[Vector, object]],
    strategy: str = "kdtree",
    cell_size: float = 1.0,
) -> SpatialIndex:
    """Build a spatial index over ``(coordinate, payload)`` pairs.

    Args:
        items: Points to index.
        strategy: ``kdtree`` (default), ``hash``, or ``bvh``.
        cell_size: Hash-grid cell size when ``strategy='hash'``.

    Returns:
        Concrete ``SpatialIndex`` implementation.
    """
    if strategy == "hash":
        return HashGridIndex(items, cell_size)
    if strategy == "bvh":
        return BVHIndex(items)
    return PointIndex(items)


def broad_phase(
    index: SpatialIndex,
    center: Vector,
    passive_world: float,
    *,
    radius_factor: float = 20.0,
    nearest_fallback: int = 64,
) -> list:
    """Query nearby candidates; fall back to nearest-K if the radius is empty.

    Args:
        index: Broad-phase index.
        center: Query origin in world space.
        passive_world: Passive snap range used to scale the query radius.
        radius_factor: Multiplier applied to ``passive_world``.
        nearest_fallback: Count used when the radius query returns nothing.

    Returns:
        Candidate payloads near ``center``.
    """
    radius = max(passive_world * radius_factor, 1e-6)
    found = index.query_radius(center, radius)
    if found:
        return found
    return index.query_nearest(center, nearest_fallback)
