"""Guide label text helpers."""

from __future__ import annotations

import math
from collections.abc import Callable

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


LengthFormat = Callable[[float], str]


def format_length(
    value: float, unit_scale: float = 1.0, fmt: LengthFormat | None = None
) -> str:
    """Format a world-space length for a guide label.

    ``fmt`` is the scene-aware formatter (e.g. ``12.3 cm``); without it the
    value is scaled by ``unit_scale`` and shown as a plain number.
    """
    if fmt is not None:
        return fmt(value)
    distance = value * unit_scale
    if abs(distance) >= 100.0:
        return f"{distance:.1f}"
    if abs(distance) >= 10.0:
        return f"{distance:.2f}"
    return f"{distance:.3f}"


def alignment_label(
    axis: str,
    target_kind,
    residual: float,
    unit_scale: float,
    fmt: LengthFormat | None = None,
) -> str:
    """Format an alignment label with its residual; ``target_kind`` is unused."""
    if residual <= 1e-6:
        return axis
    return f"{axis} · {format_length(residual, unit_scale, fmt)}"


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


def rotation_snap_label(angle_rad: float) -> str:
    """Preview text for a rotate snap, e.g. ``→ 45°`` or ``→ 7.5°``."""
    deg = f"{math.degrees(angle_rad):.1f}".rstrip("0").rstrip(".")
    return f"→ {deg}°"


def size_match_label(name: str, size_text: str) -> str:
    """Preview text for a scale snap, e.g. ``= Cube.002 · 2 m``."""
    return f"= {name} · {size_text}"
