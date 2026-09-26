"""Geometric feature dataclasses extracted from scene entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from mathutils import Vector


class FeatureType(Enum):
    """Discriminant for feature geometry kinds."""
    POINT = "point"
    LINE = "line"
    PLANE = "plane"
    DIRECTION = "direction"
    CIRCLE = "circle"
    BBOX = "bbox"
    SURFACE = "surface"


class PointKind(Enum):
    """Semantic role of a point feature."""
    ORIGIN = "origin"
    PIVOT = "pivot"
    VERTEX = "vertex"
    CENTROID = "centroid"
    BBOX_FACE_CENTER = "bbox_face_center"
    BBOX_CORNER = "bbox_corner"
    MIDPOINT = "midpoint"
    EDGE = "edge"
    FACE = "face"
    BONE = "bone"
    CURVE = "curve"


POINT_PRIORITY = {
    PointKind.ORIGIN: 100,
    PointKind.PIVOT: 95,
    PointKind.VERTEX: 98,
    PointKind.BONE: 92,
    PointKind.CENTROID: 80,
    PointKind.FACE: 78,
    PointKind.BBOX_FACE_CENTER: 70,
    PointKind.MIDPOINT: 65,
    PointKind.EDGE: 63,
    PointKind.CURVE: 62,
    PointKind.BBOX_CORNER: 60,
}


@dataclass(frozen=True)
class EntityRef:
    """Stable reference to a scene entity by name."""
    name: str
    kind: str = "object"


@dataclass(frozen=True)
class FeatureRef:
    """Typed reference to a feature on an entity."""
    entity: EntityRef
    feature_type: FeatureType
    kind: str

    @classmethod
    def for_point(cls, entity: EntityRef, kind: PointKind) -> FeatureRef:
        """Build a point FeatureRef for ``entity``."""
        return cls(entity=entity, feature_type=FeatureType.POINT, kind=kind.value)


@dataclass(frozen=True)
class PointFeature:
    """World-space point with kind and entity."""
    co: Vector
    kind: PointKind
    entity_ref: EntityRef

    @classmethod
    def from_name(cls, co: Vector, kind: PointKind, name: str) -> PointFeature:
        """Build a PointFeature at ``co`` owned by the entity ``name``."""
        return cls(co, kind, EntityRef(name=name))

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return POINT_PRIORITY[self.kind]

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.co

    @property
    def ref(self) -> FeatureRef:
        """FeatureRef for this point."""
        return FeatureRef.for_point(self.entity_ref, self.kind)

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.POINT


@dataclass(frozen=True)
class LineFeature:
    """Infinite line (point + direction) on an entity."""
    point: Vector
    direction: Vector
    kind: str
    entity_ref: EntityRef

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return 75

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.point

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.LINE


@dataclass(frozen=True)
class PlaneFeature:
    """Plane (point + normal) on an entity."""
    point: Vector
    normal: Vector
    kind: str
    entity_ref: EntityRef

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return 75

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.point

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.PLANE


@dataclass(frozen=True)
class DirectionFeature:
    """Directed axis from an origin."""
    origin: Vector
    direction: Vector
    kind: str
    entity_ref: EntityRef

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return 70

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.origin

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.DIRECTION


@dataclass(frozen=True)
class BBoxFeature:
    """Axis-aligned bounding box center and size."""
    center: Vector
    dimensions: Vector
    entity_ref: EntityRef

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return 72

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.center

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.BBOX


@dataclass(frozen=True)
class CircleFeature:
    """Circle center, normal, and radius."""
    center: Vector
    normal: Vector
    radius: float
    kind: str
    entity_ref: EntityRef

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return 68

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.center

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.CIRCLE


@dataclass(frozen=True)
class SurfaceFeature:
    """Sampled surface point with normal."""
    point: Vector
    normal: Vector
    entity_ref: EntityRef

    @property
    def entity(self) -> str:
        """Owning entity name."""
        return self.entity_ref.name

    @property
    def priority(self) -> int:
        """Ranking priority for this feature kind."""
        return 65

    @property
    def anchor(self) -> Vector:
        """World-space anchor used for proximity queries."""
        return self.point

    @property
    def feature_type(self) -> FeatureType:
        """FeatureType discriminant for this instance."""
        return FeatureType.SURFACE


Feature = PointFeature | LineFeature | PlaneFeature | DirectionFeature | BBoxFeature | CircleFeature | SurfaceFeature


def feature_anchor(feature: Feature) -> Vector:
    """Return the world-space anchor of ``feature``."""
    return feature.anchor


def feature_entity(feature: Feature) -> str:
    """Return the entity name of ``feature``."""
    return feature.entity


def feature_priority(feature: Feature) -> int:
    """Return the ranking priority of ``feature``."""
    return feature.priority


@dataclass
class FeaturePool:
    """Typed bags of features for one or more entities."""
    points: list[PointFeature] = field(default_factory=list)
    lines: list[LineFeature] = field(default_factory=list)
    planes: list[PlaneFeature] = field(default_factory=list)
    directions: list[DirectionFeature] = field(default_factory=list)
    bboxes: list[BBoxFeature] = field(default_factory=list)
    circles: list[CircleFeature] = field(default_factory=list)
    surfaces: list[SurfaceFeature] = field(default_factory=list)

    def by_type(self, ftype: FeatureType) -> list:
        """Return the list bucket for ``ftype``."""
        return {
            FeatureType.POINT: self.points,
            FeatureType.LINE: self.lines,
            FeatureType.PLANE: self.planes,
            FeatureType.DIRECTION: self.directions,
            FeatureType.BBOX: self.bboxes,
            FeatureType.CIRCLE: self.circles,
            FeatureType.SURFACE: self.surfaces,
        }.get(ftype, [])

    def anchor_items(self) -> list[tuple[Vector, Feature]]:
        """Return ``(anchor, feature)`` pairs for all features."""
        items: list[tuple[Vector, Feature]] = []
        for group in (
            self.points,
            self.lines,
            self.planes,
            self.directions,
            self.bboxes,
            self.circles,
            self.surfaces,
        ):
            for feat in group:
                items.append((feat.anchor, feat))
        return items

    def extend(self, other: FeaturePool) -> None:
        """Append all features from ``other`` into this pool."""
        self.points.extend(other.points)
        self.lines.extend(other.lines)
        self.planes.extend(other.planes)
        self.directions.extend(other.directions)
        self.bboxes.extend(other.bboxes)
        self.circles.extend(other.circles)
        self.surfaces.extend(other.surfaces)

    @classmethod
    def from_features(cls, features: list[Feature]) -> FeaturePool:
        """Build a pool by sorting features into typed buckets."""
        pool = cls()
        for feat in features:
            pool.by_type(feat.feature_type).append(feat)
        return pool
