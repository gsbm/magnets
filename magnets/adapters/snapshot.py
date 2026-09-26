"""Per-interaction scene feature cache."""

from __future__ import annotations

from ..core.features import FeaturePool
from ..core.spatial import SpatialIndex, build_point_index
from .surface import SurfaceIndex, build_surface_index


class InteractionSnapshot:
    """Cached scene features for one interaction."""
    def __init__(
        self,
        pool: FeaturePool,
        index: SpatialIndex,
        surface_index: SurfaceIndex | None = None,
    ):
        self.pool = pool
        self.index = index
        self.surface_index = surface_index

    @classmethod
    def from_context(
        cls,
        context,
        exclude,
        *,
        surfaces: bool = True,
        strategy="kdtree",
        cell_size=1.0,
        **extract_kwargs,
    ):
        """Build a snapshot from the current Blender context.

        Object features come from a cache that survives between drags (see
        ``scene_cache``), so only objects changed since the last drag are
        re-extracted.

        Args:
            context: Blender context.
            exclude: Objects to skip.
            surfaces: Collect surface candidates (only tangency needs them).
            strategy: Spatial index strategy.
            cell_size: Hash-grid cell size.
            **extract_kwargs: Forwarded to feature extractors.

        Returns:
            InteractionSnapshot instance.
        """
        from .extract import candidate_feature_pool

        pool = candidate_feature_pool(context, exclude, **extract_kwargs)
        index = build_point_index(pool.anchor_items(), strategy=strategy, cell_size=cell_size)
        surface_index = build_surface_index(context, exclude) if surfaces else None
        return cls(pool, index, surface_index)
