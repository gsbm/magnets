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
    # World view direction of an orthographic view (None in perspective).
    # Solvers may skip what ``view_filter`` would hide in this view anyway.
    view_normal: Vector | None = None
    # Emit only the lowest-residual relationship per rank key (family, axis,
    # target entity, moving kind, target kind) instead of every pair.
    best_per_key: bool = False
    # (moving_co, correction) -> screen distance in px, or None off-screen.
    # Lets best-per-key solvers rank candidates exactly as ranking will.
    screen_dist: Callable[[Vector, Vector], float | None] | None = None

    def rank_order(self, family: str, moving, residual: float, moving_co, correction):
        """Sort value ``scoring.rank`` gives a relationship (lower sorts first).

        None when it would be dropped (off-screen or beyond the passive range).
        Without ``screen_dist`` the residual stands in for it.
        """
        if self.screen_dist is None:
            return (residual,)
        sd = self.screen_dist(moving_co, correction)
        if sd is None or sd > self.passive_px:
            return None
        score = score_parts(
            family, feature_priority(moving), residual, sd, self.passive_px, self.world_tol
        )
        return (-score, sd)

    def direction_hidden(self, direction: Vector) -> bool:
        """True when the view filter hides a snap/guide along ``direction``."""
        if self.view_normal is None:
            return False
        return not guide_direction_visible(direction, self.view_normal)

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
