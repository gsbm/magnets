"""Guide label text helpers."""

from __future__ import annotations

from .features import (
    BBoxFeature,
    CircleFeature,
    DirectionFeature,
    Feature,
    LineFeature,
    PlaneFeature,
    PointFeature,
    PointKind,
    SurfaceFeature,
)


def point_kind_label(kind: PointKind) -> str:
    """Short UI label for a PointKind."""
    return {
        PointKind.ORIGIN: "origin",
        PointKind.PIVOT: "pivot",
        PointKind.CENTROID: "center",
        PointKind.BBOX_FACE_CENTER: "face",
        PointKind.BBOX_CORNER: "corner",
        PointKind.MIDPOINT: "midpoint",
        PointKind.VERTEX: "vertex",
        PointKind.BONE: "bone",
        PointKind.FACE: "face",
        PointKind.CURVE: "curve",
    }.get(kind, kind.value)


def alignment_label(axis: str, target_kind, residual: float, unit_scale: float) -> str:
    """Format an alignment guide label with optional distance.

    Args:
        axis: Axis name (X/Y/Z).
        target_kind: Target PointKind (unused in text; reserved).
        residual: World-space residual.
        unit_scale: Scene unit scale for display.

    Returns:
        Label string.
    """
    base = axis
    if residual <= 1e-6:
        return base
    distance = residual * unit_scale
    if distance >= 100.0:
        return f"{base} · {distance:.1f}"
    if distance >= 10.0:
        return f"{base} · {distance:.2f}"
    return f"{base} · {distance:.3f}"


def feature_hint(feature: Feature) -> str:
    """Short hint string describing a feature."""
    if isinstance(feature, PointFeature):
        return point_kind_label(feature.kind)
    if isinstance(feature, LineFeature):
        return feature.kind.replace("_", " ")
    if isinstance(feature, PlaneFeature):
        return feature.kind.replace("_", " ")
    if isinstance(feature, DirectionFeature):
        return feature.kind.replace("_", " ")
    if isinstance(feature, BBoxFeature):
        return "bbox"
    if isinstance(feature, CircleFeature):
        return feature.kind.replace("_", " ")
    if isinstance(feature, SurfaceFeature):
        return "surface"
    return ""
