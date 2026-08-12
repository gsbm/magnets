"""Passive/active snap thresholds with break-away hysteresis."""

from __future__ import annotations

from dataclasses import dataclass, field

from .scoring import RankItem


@dataclass
class SnapHysteresis:
    """Engage / hold / break latch for the active guide."""
    active_key: tuple | None = None
    broken: bool = False
    _miss_frames: int = 0
    _latched: RankItem | None = field(default=None, repr=False)
    _sticky_keys: set[tuple] = field(default_factory=set, repr=False)

    def reset(self) -> None:
        """Clear latch and sticky state."""
        self.active_key = None
        self.broken = False
        self._miss_frames = 0
        self._latched = None
        self._sticky_keys = set()

    def remember_active_keys(self, keys: set[tuple]) -> None:
        """Store keys for sticky re-attachment."""
        if keys:
            self._sticky_keys = set(keys)

    @property
    def sticky_keys(self) -> set[tuple]:
        """Keys remembered for sticky re-attachment."""
        return self._sticky_keys

    def force_break(self) -> None:
        """Release latch immediately (user dragged beyond break distance)."""
        self.active_key = None
        self._latched = None
        self._sticky_keys = set()
        self.broken = True
        self._miss_frames = 0

    def pick_active(
        self,
        ranked: list[RankItem],
        snap_px: float,
        hysteresis_px: float,
        *,
        visible: list[RankItem] | None = None,
        reengage_margin_px: float = 4.0,
    ) -> tuple[RankItem | None, bool]:
        """Return ``(active_item, is_snapped)`` for this frame.

        ``ranked`` is the decluttered top-K used for new engagements.
        ``visible`` is the full in-range set used to hold an existing latch
        (so a guide does not drop when it falls out of top-K for one frame).
        """
        release_px = snap_px + hysteresis_px
        lookup = visible if visible is not None else ranked

        if not ranked and not lookup:
            self.reset()
            return None, False

        best = ranked[0] if ranked else None

        if self.broken:
            probe = best or (lookup[0] if lookup else None)
            if probe is not None and probe.screen_dist > snap_px + reengage_margin_px:
                self.broken = False
            else:
                return None, False

        if self.active_key is not None:
            current = next((it for it in lookup if it.key == self.active_key), None)
            if current is None:
                self._miss_frames += 1
                if self._miss_frames < 4 and self._latched is not None:
                    return self._latched, True
                self.active_key = None
                self._latched = None
                self._miss_frames = 0
                self._sticky_keys = set()
                self.broken = True
                return None, False
            self._miss_frames = 0
            self._latched = current
            if current.screen_dist <= release_px:
                return current, True
            self.active_key = None
            self._latched = None
            self._sticky_keys = set()
            self.broken = True
            return None, False

        if best is not None and best.screen_dist <= snap_px:
            self.active_key = best.key
            self._latched = best
            self.broken = False
            self._miss_frames = 0
            return best, True

        return None, False
