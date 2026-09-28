"""Relationship and ConstraintDelta types produced by solvers."""

from __future__ import annotations

from dataclasses import dataclass, field

from mathutils import Vector

from .features import Feature, PointFeature, feature_anchor, feature_priority


@dataclass
class ConstraintDelta:
    """Transform correction produced by a solver."""
    translation: Vector = field(default_factory=lambda: Vector((0.0, 0.0, 0.0)))
    rotation_axis: Vector = field(default_factory=lambda: Vector((0.0, 0.0, 1.0)))
    rotation_angle: float = 0.0
    scale_factor: float = 1.0
    scale_axis: Vector = field(default_factory=lambda: Vector((1.0, 1.0, 1.0)))

    @classmethod
    def from_vector(cls, v: Vector) -> ConstraintDelta:
        """Build a translation-only ConstraintDelta."""
        return cls(translation=v.copy())

    @classmethod
    def from_rotation(cls, axis: Vector, angle: float) -> ConstraintDelta:
        """Build a rotation ConstraintDelta (``angle`` in radians)."""
        return cls(rotation_axis=axis.copy(), rotation_angle=angle)

    @classmethod
    def from_scale(cls, factor: float) -> ConstraintDelta:
        """Build a uniform scale ConstraintDelta."""
        return cls(scale_factor=factor, scale_axis=Vector((factor, factor, factor)))


@dataclass
class GuideLine:
    """Infinite guide line for drawing."""
    point: Vector
    direction: Vector


@dataclass
class GuideSegment:
    """Finite guide segment for drawing."""
    a: Vector
    b: Vector


@dataclass
class GuideCircle:
    """Circular guide for drawing."""
    center: Vector
    normal: Vector
    radius: float


@dataclass
class GuidePlane:
    """Plane guide (drawn as a cross)."""
    point: Vector
    normal: Vector


@dataclass
class GuideSpans:
    """Equal-gap measurement bars for distribution guides.

    ``gaps`` are endpoint pairs; ``axis`` orients badge ticks and view culling.
    """

    gaps: tuple[tuple[Vector, Vector], ...]
    axis: Vector


Guide = GuideLine | GuideSegment | GuideCircle | GuidePlane | GuideSpans


@dataclass
class Relationship:
    """Scored candidate constraint between features."""
    family: str
    axis: str
    label: str  # or a zero-argument callable returning it (see below)
    moving: Feature
    targets: tuple[Feature, ...]
    residual: float
    delta: ConstraintDelta
    guide: Guide
    base_priority: int = 0
    # Unit direction this relationship pins (alignment axis, plane normal), so
    # a satisfied constraint keeps it. None: use the delta's own direction.
    constraint_dir: Vector | None = None

    def __post_init__(self):
        if not self.base_priority:
            self.base_priority = feature_priority(self.moving)

    @property
    def target(self) -> Feature:
        """Primary target feature."""
        return self.targets[0]

    @property
    def target_entity(self) -> str:
        """Entity name of the primary target."""
        from .features import feature_entity

        return feature_entity(self.targets[0])

    @property
    def moving_co(self) -> Vector:
        """World anchor of the moving feature."""
        return feature_anchor(self.moving)

    @property
    def translation(self) -> Vector:
        """Translation component of ``delta``."""
        return self.delta.translation

    # Compatibility aliases for point-only relationships.
    @property
    def moving_point(self) -> PointFeature | None:
        """Moving feature if it is a PointFeature, else None."""
        return self.moving if isinstance(self.moving, PointFeature) else None


def _get_label(self) -> str:
    label = self.__dict__["_label"]
    if callable(label):
        label = self.__dict__["_label"] = label()
    return label


def _set_label(self, value) -> None:
    self.__dict__["_label"] = value


# ``label`` may be given as a zero-argument callable: it runs on first read and
# the text is cached. Only drawn guides are ever read, so hot solvers pass one
# instead of formatting a length for every candidate.
Relationship.label = property(_get_label, _set_label, doc="Guide label text.")
