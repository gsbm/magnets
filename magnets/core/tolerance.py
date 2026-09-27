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
    # The guide that broke away. Only it must leave the snap zone before it
    # may engage again; other guides stay free to engage meanwhile.
    _broken_key: tuple | None = field(default=None, repr=False)

    def reset(self) -> None:
        """Clear latch and sticky state."""
        self.active_key = None
        self.broken = False
        self._miss_frames = 0
        self._latched = None
        self._sticky_keys = set()
        self._broken_key = None

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
        self._break()

    def _break(self) -> None:
        self._broken_key = self.active_key
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
            reengage_px = snap_px + reengage_margin_px
            if self._broken_key is None:
                # Unknown culprit: wait for the best candidate to leave.
                probe = best or (lookup[0] if lookup else None)
                if probe is not None and probe.screen_dist > reengage_px:
                    self.broken = False
                else:
                    return None, False
            else:
                culprit = next(
                    (it for it in lookup if it.key == self._broken_key), None
                )
                if culprit is None or culprit.screen_dist > reengage_px:
                    self.broken = False
                    self._broken_key = None

        if self.active_key is not None:
            current = next((it for it in lookup if it.key == self.active_key), None)
            if current is None:
                # The latched guide vanished. A different guide already in the
                # snap zone takes over (the selection jumped: typed input or a
                # fast flick); holding the stale latch would block it.
                blocked = self._broken_key if self.broken else None
                fresh = next(
                    (
                        it
                        for it in ranked
                        if it.screen_dist <= snap_px and it.key != blocked
                    ),
                    None,
                )
                if fresh is not None:
                    self.active_key = fresh.key
                    self._latched = fresh
                    self._miss_frames = 0
                    return fresh, True
                self._miss_frames += 1
                if self._miss_frames < 4 and self._latched is not None:
                    return self._latched, True
                self._break()
                return None, False
            self._miss_frames = 0
            self._latched = current
            if snap_px < current.screen_dist <= release_px:
                # Held only by the hysteresis band: a different guide inside
                # the snap zone is what the selection is actually on, so it
                # takes over rather than losing to a far, sticky one.
                blocked = self._broken_key if self.broken else None
                rival = next(
                    (
                        it
                        for it in ranked
                        if it.screen_dist <= snap_px
                        and it.key not in (self.active_key, blocked)
                    ),
                    None,
                )
                if rival is not None:
                    self.active_key = rival.key
                    self._latched = rival
                    return rival, True
            if current.screen_dist <= release_px:
                return current, True
            self._break()
            return None, False

        # Engage the closest in-zone guide, skipping one still breaking away.
        blocked = self._broken_key if self.broken else None
        pick = next(
            (
                it
                for it in ranked
                if it.screen_dist <= snap_px and it.key != blocked
            ),
            None,
        )
        if pick is not None:
            self.active_key = pick.key
            self._latched = pick
            self._miss_frames = 0
            return pick, True

        return None, False
