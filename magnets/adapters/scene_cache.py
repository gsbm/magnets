"""Scene feature and surface caches that survive between drags.

Starting a drag used to re-extract features for every visible object and build
a BVH for every visible mesh (~140 ms on a 400-object scene). Both are now
cached across drags:

- **Object features** (mesh objects) depend only on ``matrix_world`` and
  ``bound_box`` (see ``extract.object_feature_pool``), so an entry is reused
  while that fingerprint and the extraction options are unchanged.
- **Surface BVHs** are built lazily, in object-local space, only for objects a
  query actually reaches. Moving an object does not invalidate its BVH; a
  geometry change (reported by the depsgraph) or undo / file load does.
"""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from ..core.features import FeaturePool

try:
    from mathutils.bvhtree import BVHTree

    _HAVE_BVH = True
except ImportError:  # pragma: no cover
    _HAVE_BVH = False

# pointer -> (fingerprint, FeaturePool)
_features: dict[int, tuple[tuple, FeaturePool]] = {}
# pointer -> (bound_box fingerprint, BVHTree | None)
_bvhs: dict[int, tuple[tuple, object]] = {}
# Objects whose evaluated geometry changed since their BVH was built.
_geometry_dirty: set[int] = set()


class _Stats:
    """Counters for tests and debug logging."""

    feature_hits = 0
    feature_misses = 0
    bvh_builds = 0

    @classmethod
    def reset(cls) -> None:
        cls.feature_hits = cls.feature_misses = cls.bvh_builds = 0


stats = _Stats


def clear() -> None:
    """Drop every cached entry."""
    _features.clear()
    _bvhs.clear()
    _geometry_dirty.clear()


def _bound_box_key(obj) -> tuple:
    return tuple(tuple(corner) for corner in obj.bound_box)


def _fingerprint(obj, options_key: tuple) -> tuple:
    return (
        obj.name,
        tuple(tuple(row) for row in obj.matrix_world),
        _bound_box_key(obj),
        options_key,
    )


def object_features(obj, **extract_kwargs) -> FeaturePool:
    """Features of ``obj``, reused while its transform and bounds are unchanged.

    Args:
        obj: Blender object.
        **extract_kwargs: Extraction options (part of the cache key).

    Returns:
        The cached or freshly extracted FeaturePool. Treat it as read-only.
    """
    from .entities import entity_feature_pool

    # Only meshes are cached: their features derive from matrix + bounds alone.
    # Curves/armatures read their data points and are few; extract directly.
    if obj.type != "MESH":
        return entity_feature_pool(obj, **extract_kwargs)
    key = obj.as_pointer()
    fingerprint = _fingerprint(obj, tuple(sorted(extract_kwargs.items())))
    hit = _features.get(key)
    if hit is not None and hit[0] == fingerprint:
        stats.feature_hits += 1
        return hit[1]
    stats.feature_misses += 1
    pool = entity_feature_pool(obj, **extract_kwargs)
    _features[key] = (fingerprint, pool)
    return pool


def prune(alive_pointers: set[int]) -> None:
    """Forget entries for objects that no longer exist."""
    for cache in (_features, _bvhs):
        for key in [k for k in cache if k not in alive_pointers]:
            del cache[key]


def object_bvh(obj, depsgraph):
    """Local-space BVH of ``obj``'s evaluated mesh, built on first use.

    Returns None for non-meshes and empty meshes.
    """
    if not _HAVE_BVH or obj.type != "MESH" or obj.data is None:
        return None
    key = obj.as_pointer()
    bounds = _bound_box_key(obj)
    hit = _bvhs.get(key)
    if hit is not None and hit[0] == bounds and key not in _geometry_dirty:
        return hit[1]
    tree = None
    if len(obj.data.vertices):
        tree = BVHTree.FromObject(obj.evaluated_get(depsgraph), depsgraph)
        stats.bvh_builds += 1
    _bvhs[key] = (bounds, tree)
    _geometry_dirty.discard(key)
    return tree


@persistent
def _on_depsgraph_update(_scene, depsgraph):
    for update in depsgraph.updates:
        if update.is_updated_geometry and isinstance(update.id, bpy.types.Object):
            _geometry_dirty.add(update.id.original.as_pointer())


@persistent
def _on_reset(*_args):
    # Undo/redo/load re-create datablocks: pointers and geometry may change.
    clear()


_HANDLERS = (
    ("depsgraph_update_post", _on_depsgraph_update),
    ("undo_post", _on_reset),
    ("redo_post", _on_reset),
    ("load_post", _on_reset),
)


def register():
    """Install the cache-invalidation handlers."""
    for name, fn in _HANDLERS:
        handlers = getattr(bpy.app.handlers, name)
        if fn not in handlers:
            handlers.append(fn)


def unregister():
    """Remove the handlers and drop cached data."""
    for name, fn in _HANDLERS:
        handlers = getattr(bpy.app.handlers, name)
        if fn in handlers:
            handlers.remove(fn)
    clear()
