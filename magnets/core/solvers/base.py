"""Solver ABC and shared ``SolveContext``."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from mathutils import Vector

from ..features import FeatureType, feature_priority
from ..frames import Frame
from ..labels import LengthFormat, format_length
from ..relationship import Relationship
from ..scoring import score_parts
from ..transform import TransformMode
from ..view_filter import guide_direction_visible


@dataclass
class SolveContext:
    """Shared parameters passed to every solver invocation."""

    axes: dict[str, Vector]
    world_tol: float
    frame: Frame = Frame.WORLD
    passive_px: float = 48.0
    snap_px: float = 12.0
    unit_scale: float = 1.0
    surface_query_limit: int = 8
    transform_mode: TransformMode = TransformMode.TRANSLATE
    # Distribution gap metric: "center", "edge", or "both".
    spacing_metric: str = "both"
    # Scene-aware length formatter for labels (e.g. "12.3 cm"); None falls back
    # to a plain number scaled by ``unit_scale``.
    length_format: LengthFormat | None = None
    # Depth direction: the view direction of an orthographic view, or the
    # view ray through the selection in perspective (None: no depth filter).
    # Solvers may skip what ``view_filter`` would hide in this view anyway.
    view_normal: Vector | None = None
    # ``view_filter`` parallel threshold for ``view_normal`` (Depth Axis Cutoff).
    depth_threshold: float = 0.15
    # (moving_co, correction) -> screen distance in px, or None off-screen.
    # Lets best-per-key solvers rank candidates exactly as ranking will.
    screen_dist: Callable[[Vector, Vector], float | None] | None = None
    # (4x4 perspective matrix rows, region width, region height) of the same
    # view, for vectorised approximations of ``screen_dist``.
    projection: tuple | None = None
    # Optional screen cutoff (px) tighter than ``passive_px``; scoring is
    # unchanged. Used for far objects, which only show guides near snapping.
    max_screen_px: float | None = None
    # Pair solvers (midpoint, own-size spacing) also use pairs of points that
    # lie diagonally; False keeps pairs running along one of ``axes``.
    allow_diagonal: bool = True

    @property
    def screen_limit(self) -> float:
        """Screen distance beyond which a relationship is dropped."""
        if self.max_screen_px is None:
            return self.passive_px
        return min(self.passive_px, self.max_screen_px)

    def rank_order(self, family: str, moving, residual: float, moving_co, correction):
        """Sort value ``scoring.rank`` gives a relationship (lower sorts first).

        None when it would be dropped (off-screen or beyond the passive range).
        Without ``screen_dist`` the residual stands in for it.
        """
        if self.screen_dist is None:
            return (residual,)
        sd = self.screen_dist(moving_co, correction)
        if sd is None or sd > self.screen_limit:
            return None
        score = score_parts(
            family, feature_priority(moving), residual, sd, self.passive_px, self.world_tol
        )
        return (-score, sd)

    def direction_hidden(self, direction: Vector) -> bool:
        """True when the view filter hides a snap/guide along ``direction``."""
        if self.view_normal is None:
            return False
        return not guide_direction_visible(
            direction, self.view_normal, parallel_threshold=self.depth_threshold
        )

    def format_length(self, value: float) -> str:
        """Format a world-space length for a guide label."""
        return format_length(value, self.unit_scale, self.length_format)


class BestPerKey:
    """Lowest-residual candidate per key, returned in first-visit order.

    Solvers offer cheap tuples and build Relationship objects only for the
    winners. Ties keep the earliest offer.
    """

    def __init__(self):
        self._best: dict = {}
        self._seq = 0

    def offer(self, key, order, data) -> None:
        """Keep ``data`` for ``key`` if ``order`` sorts before the current best.

        ``order`` is a residual or a ``SolveContext.rank_order`` value; None
        (the item would be dropped) is ignored.
        """
        if order is None:
            self._seq += 1
            return
        cur = self._best.get(key)
        if cur is None or order < cur[0]:
            self._best[key] = (order, self._seq, data)
        self._seq += 1

    def winners(self) -> list:
        """The kept ``data`` of every key, in the order they were offered."""
        return [data for _res, _seq, data in sorted(self._best.values(), key=lambda t: t[1])]


class Solver(ABC):
    """Abstract geometric constraint solver."""

    family: str

    def consumes(self, a: FeatureType, b: FeatureType) -> bool:
        """Return True if this solver handles the unordered pair ``(a, b)``."""
        want = self.feature_types()
        return (a, b) == want or (b, a) == want

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver expects."""
        return (FeatureType.POINT, FeatureType.POINT)

    @abstractmethod
    def solve(
        self,
        moving,
        candidates,
        ctx: SolveContext,
    ) -> list[Relationship]:
        """Evaluate ``moving`` against ``candidates`` and return relationships."""
