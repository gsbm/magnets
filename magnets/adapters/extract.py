"""Convert scene entities into core Feature pools."""

from __future__ import annotations

from mathutils import Vector

from ..core.bbox import (
    bbox_bounding_sphere,
    bbox_centroid,
    bbox_dimensions,
    bbox_edges,
    bbox_face_centers,
    bbox_face_planes,
)
from ..core.features import (
    BBoxFeature,
    CircleFeature,
    DirectionFeature,
    EntityRef,
    FeaturePool,
    LineFeature,
    PlaneFeature,
    PointFeature,
    PointKind,
)


def _local_corners(obj) -> list[Vector]:
    return [Vector(corner) for corner in obj.bound_box]


def object_feature_pool(
    obj,
    *,
    use_origin: bool = True,
    use_pivot: bool = True,
    use_corners: bool = True,
    use_face_centers: bool = True,
    use_centroid: bool = True,
    use_edges: bool = True,
    use_face_planes: bool = True,
    use_axes: bool = True,
    use_bbox: bool = True,
    use_circles: bool = True,
) -> FeaturePool:
    """Extract a FeaturePool for one Blender object.

    Args:
        obj: Blender object.
        use_origin: Include object origin.
        use_pivot: Include pivot point.
        use_corners: Include bbox corners.
        use_face_centers: Include bbox face centers.
        use_centroid: Include bbox centroid.
        use_edges: Include bbox edges as lines.
        use_face_planes: Include bbox face planes.
        use_axes: Include local axes as directions.
        use_bbox: Include BBoxFeature.
        use_circles: Include derived circle features when applicable.

    Returns:
        FeaturePool for ``obj``.
    """
    mw = obj.matrix_world
    ref = EntityRef(name=obj.name)
    pool = FeaturePool()

    if use_origin:
        pool.points.append(PointFeature(mw.translation.copy(), PointKind.ORIGIN, ref))
    if use_pivot:
        pool.points.append(PointFeature(mw.translation.copy(), PointKind.PIVOT, ref))

    corners_local = _local_corners(obj)
    if not corners_local:
        return pool

    corners_world = [mw @ c for c in corners_local]

    if use_corners:
        for co in corners_world:
            pool.points.append(PointFeature(co, PointKind.BBOX_CORNER, ref))

    if use_face_centers:
        for co_local in bbox_face_centers(corners_local):
            pool.points.append(PointFeature(mw @ co_local, PointKind.BBOX_FACE_CENTER, ref))

    if use_centroid:
        centroid_local = bbox_centroid(corners_local)
        if centroid_local is not None:
            pool.points.append(PointFeature(mw @ centroid_local, PointKind.CENTROID, ref))

    if use_edges:
        for a_local, b_local in bbox_edges(corners_local):
            a = mw @ a_local
            b = mw @ b_local
            direction = b - a
            if direction.length_squared == 0.0:
                continue
            pool.lines.append(
                LineFeature(a.copy(), direction.normalized(), "bbox_edge", ref)
            )

    if use_face_planes:
        for center_local, normal_local in bbox_face_planes(corners_local):
            normal_world = (mw.to_3x3() @ normal_local).normalized()
            pool.planes.append(
                PlaneFeature(mw @ center_local, normal_world, "bbox_face", ref)
            )

    if use_axes:
        for idx, axis_name in enumerate(("X", "Y", "Z")):
            direction = (mw.to_3x3().col[idx]).to_3d().normalized()
            pool.directions.append(
                DirectionFeature(mw.translation.copy(), direction, f"axis_{axis_name}", ref)
            )

    if use_bbox:
        dims_local = bbox_dimensions(corners_local)
        if dims_local is not None:
            scale = Vector(mw.to_3x3().col[i].length for i in range(3))
            pool.bboxes.append(
                BBoxFeature(
                    center=mw @ bbox_centroid(corners_local),
                    dimensions=dims_local * scale,
                    entity_ref=ref,
                )
            )

    if use_circles:
        sphere = bbox_bounding_sphere(corners_local)
        if sphere is not None:
            center_local, radius_local = sphere
            scale_avg = sum(mw.to_3x3().col[i].length for i in range(3)) / 3.0
            pool.circles.append(
                CircleFeature(
                    center=mw @ center_local,
                    normal=(mw.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized(),
                    radius=radius_local * scale_avg,
                    kind="bbox_sphere",
                    entity_ref=ref,
                )
            )

    return pool


def object_point_features(obj, **kwargs) -> list[PointFeature]:
    """Extract point features for one object.

    Args:
        obj: Blender object.
        **kwargs: Forwarded to ``object_feature_pool``.

    Returns:
        List of PointFeature values.
    """
    return object_feature_pool(obj, **kwargs).points


def candidate_feature_pool(context, exclude, **kwargs) -> FeaturePool:
    """Build a FeaturePool for candidate objects in the view layer.

    Args:
        context: Blender context.
        exclude: Objects to skip.
        **kwargs: Forwarded to ``entity_feature_pool``.

    Returns:
        Combined FeaturePool.
    """
    from .entities import entity_feature_pool

    exclude_names = {o.name for o in exclude}
    pool = FeaturePool()
    for obj in context.view_layer.objects:
        if obj.name in exclude_names or not obj.visible_get():
            continue
        pool.extend(entity_feature_pool(obj, **kwargs))
    return pool


def candidate_features(context, exclude, **kwargs) -> list[PointFeature]:
    """Flatten candidate point features for proximity queries.

    Args:
        context: Blender context.
        exclude: Objects to skip.
        **kwargs: Forwarded to extractors.

    Returns:
        Flat list of PointFeature values.
    """
    return candidate_feature_pool(context, exclude, **kwargs).points
