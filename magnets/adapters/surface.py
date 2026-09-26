"""BVH surface sampling for tangency and surface offset."""

from __future__ import annotations

from mathutils import Vector

from ..core.features import EntityRef, FeaturePool, SurfaceFeature


class SurfaceIndex:
    """Nearest-on-surface queries against candidate meshes.

    Stores a world bounding sphere per candidate; a mesh's BVH is built (and
    cached) only once a query comes within reach of it.
    """

    def __init__(self, candidates: list[tuple[object, Vector, float]], depsgraph):
        self._candidates = candidates  # (object, world center, world radius)
        self._depsgraph = depsgraph

    def __len__(self) -> int:
        return len(self._candidates)

    def query_nearest(
        self,
        co: Vector,
        max_dist: float,
        limit: int = 8,
    ) -> list[SurfaceFeature]:
        """Return up to ``limit`` surface samples within ``max_dist``, nearest first."""
        from . import scene_cache

        hits: list[tuple[float, SurfaceFeature]] = []
        for obj, center, radius in self._candidates:
            if (co - center).length - radius > max_dist:
                continue
            tree = scene_cache.object_bvh(obj, self._depsgraph)
            if tree is None:
                continue
            sample = _nearest_world(obj, tree, co, max_dist)
            if sample is not None:
                hits.append(sample)
        hits.sort(key=lambda h: h[0])
        return [feature for _dist, feature in hits[:limit]]


def _nearest_world(obj, tree, co: Vector, max_dist: float):
    """World-space nearest point on ``obj`` via its local-space BVH.

    ``BVHTree.FromObject`` builds in object space, so the query point goes in
    through the inverse matrix and the hit comes back out through the matrix.
    """
    mw = obj.matrix_world
    try:
        inv = mw.inverted()
    except ValueError:  # degenerate (zero) scale
        return None
    basis = mw.to_3x3()
    min_scale = min(basis.col[i].length for i in range(3))
    if min_scale <= 1e-12:
        return None
    # A world radius r covers at most r / min_scale in local units.
    loc, normal, _index, _dist = tree.find_nearest(inv @ co, max_dist / min_scale)
    if loc is None:
        return None
    point = mw @ loc
    dist = (point - co).length
    if dist > max_dist:
        return None
    normal_world = (inv.to_3x3().transposed() @ normal).normalized()
    return dist, SurfaceFeature(
        point=point,
        normal=normal_world,
        entity_ref=EntityRef(name=obj.name),
    )


def build_surface_index(context, exclude) -> SurfaceIndex | None:
    """Collect candidate meshes for surface queries, or None if there are none.

    No BVH is built here. Edit Mode objects are skipped: their geometry changes
    on every tick.
    """
    exclude_names = {o.name for o in exclude}
    candidates: list[tuple[object, Vector, float]] = []
    for obj in context.view_layer.objects:
        if obj.name in exclude_names or not obj.visible_get():
            continue
        if obj.type != "MESH" or obj.data is None or obj.mode == "EDIT":
            continue
        mw = obj.matrix_world
        corners = [mw @ Vector(c) for c in obj.bound_box]
        center = sum(corners, Vector()) / 8.0
        radius = max((c - center).length for c in corners)
        candidates.append((obj, center, radius))
    if not candidates:
        return None
    return SurfaceIndex(candidates, context.evaluated_depsgraph_get())


def surface_features_for_point(
    index: SurfaceIndex | None,
    co: Vector,
    max_dist: float,
    limit: int = 8,
) -> list[SurfaceFeature]:
    """Return up to ``limit`` surface samples within ``max_dist`` of ``co``."""
    if index is None:
        return []
    return index.query_nearest(co, max_dist, limit=limit)


def append_surfaces(pool: FeaturePool, surfaces: list[SurfaceFeature]) -> None:
    """Append ``surfaces`` to ``pool``."""
    pool.surfaces.extend(surfaces)
