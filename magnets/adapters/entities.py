"""Feature extractors for non-mesh object types."""

from __future__ import annotations

from mathutils import Vector

from ..core.features import (
    DirectionFeature,
    EntityRef,
    FeaturePool,
    LineFeature,
    PointFeature,
    PointKind,
)
from .extract import object_feature_pool


def _origin_pool(obj) -> FeaturePool:
    ref = EntityRef(name=obj.name)
    pool = FeaturePool()
    pool.points.append(
        PointFeature(obj.matrix_world.translation.copy(), PointKind.ORIGIN, ref)
    )
    return pool


def armature_feature_pool(obj) -> FeaturePool:
    """Extract bone head/tail features from an armature."""
    pool = FeaturePool()
    if obj.type != "ARMATURE" or obj.data is None:
        return pool
    ref = EntityRef(name=obj.name)
    mw = obj.matrix_world
    for bone in obj.data.bones:
        head = mw @ bone.head_local
        tail = mw @ bone.tail_local
        pool.points.append(PointFeature(head, PointKind.BONE, ref))
        direction = tail - head
        if direction.length_squared > 0.0:
            pool.lines.append(
                LineFeature(head.copy(), direction.normalized(), "bone", ref)
            )
    if not pool.points:
        pool.extend(_origin_pool(obj))
    return pool


def curve_feature_pool(obj) -> FeaturePool:
    """Extract features from a curve object."""
    pool = FeaturePool()
    if obj.type not in {"CURVE", "SURFACE", "FONT"} or obj.data is None:
        return pool
    ref = EntityRef(name=obj.name)
    mw = obj.matrix_world
    data = obj.data
    for spline in data.splines:
        points = spline.bezier_points if spline.type == "BEZIER" else spline.points
        for pt in points:
            # Poly/NURBS points are 4D (x, y, z, weight); bezier points are 3D.
            co = Vector(pt.co[:3])
            pool.points.append(PointFeature(mw @ co, PointKind.CURVE, ref))
    if not pool.points:
        pool.extend(_origin_pool(obj))
    return pool


def light_camera_empty_pool(obj) -> FeaturePool:
    """Extract origin features for light/camera/empty."""
    pool = _origin_pool(obj)
    ref = EntityRef(name=obj.name)
    mw = obj.matrix_world
    if obj.type == "LIGHT" and obj.data is not None:
        direction = (mw.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
        pool.directions.append(
            DirectionFeature(mw.translation.copy(), direction, "light_axis", ref)
        )
    elif obj.type == "CAMERA" and obj.data is not None:
        direction = (mw.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
        pool.directions.append(
            DirectionFeature(mw.translation.copy(), direction, "camera_axis", ref)
        )
    return pool


def entity_feature_pool(obj, **kwargs) -> FeaturePool:
    """Extract features for ``obj`` by type; ``kwargs`` go to mesh extractors."""
    if obj.type == "MESH":
        return object_feature_pool(obj, **kwargs)
    if obj.type == "ARMATURE":
        return armature_feature_pool(obj)
    if obj.type in {"CURVE", "SURFACE", "FONT"}:
        return curve_feature_pool(obj)
    if obj.type in {"LIGHT", "CAMERA", "EMPTY", "LATTICE"}:
        return light_camera_empty_pool(obj)
    return _origin_pool(obj)
