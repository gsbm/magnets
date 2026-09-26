"""BVH surface sampling for tangency and surface offset."""

from __future__ import annotations

from mathutils import Vector

from ..core.features import EntityRef, FeaturePool, SurfaceFeature

try:
    from mathutils.bvhtree import BVHTree

    _HAVE_BVH = True
except ImportError:  # pragma: no cover
    _HAVE_BVH = False


class SurfaceIndex:
    """Nearest-on-surface queries against cached mesh BVHs."""

    def __init__(self, items: list[tuple[object, object]]):
        self._entries = items

    def __len__(self) -> int:
        return len(self._entries)

    def query_nearest(
        self,
        co: Vector,
        max_dist: float,
        limit: int = 8,
    ) -> list[SurfaceFeature]:
        """Return nearest surface samples to ``point``.

        Args:
            point: World-space query point.
            limit: Maximum samples to return.

        Returns:
            List of SurfaceFeature samples.
        """
        out: list[SurfaceFeature] = []
        for obj, tree in self._entries:
            if len(out) >= limit:
                break
            loc, normal, _index, dist = tree.find_nearest(co, max_dist)
            if loc is None or dist is None or dist > max_dist:
                continue
            out.append(
                SurfaceFeature(
                    point=loc.copy(),
                    normal=normal.copy(),
                    entity_ref=EntityRef(name=obj.name),
                )
            )
        return out


def build_surface_index(context, exclude) -> SurfaceIndex | None:
    """Build a SurfaceIndex for candidate meshes.

    Args:
        objects: Mesh objects to index.
        depsgraph: Optional depsgraph for evaluated meshes.

    Returns:
        SurfaceIndex instance.
    """
    if not _HAVE_BVH:
        return None
    exclude_names = {o.name for o in exclude}
    items: list[tuple[object, object]] = []
    depsgraph = context.evaluated_depsgraph_get()
    for obj in context.view_layer.objects:
        if obj.name in exclude_names or not obj.visible_get():
            continue
        if obj.type != "MESH" or obj.data is None:
            continue
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        try:
            if not mesh.vertices:
                continue
            tree = BVHTree.FromObject(eval_obj, depsgraph)
            items.append((obj, tree))
        finally:
            eval_obj.to_mesh_clear()
    if not items:
        return None
    return SurfaceIndex(items)


def surface_features_for_point(
    index: SurfaceIndex | None,
    co: Vector,
    max_dist: float,
    limit: int = 8,
) -> list[SurfaceFeature]:
    """Nearest surface samples near a point.

    Args:
        index: SurfaceIndex to query.
        point: World-space query point.
        limit: Maximum samples.

    Returns:
        List of SurfaceFeature values.
    """
    if index is None:
        return []
    return index.query_nearest(co, max_dist, limit=limit)


def append_surfaces(pool: FeaturePool, surfaces: list[SurfaceFeature]) -> None:
    """Append surface features into a FeaturePool.

    Args:
        pool: Destination FeaturePool.
        features: Surface features to append.
    """
    pool.surfaces.extend(surfaces)
