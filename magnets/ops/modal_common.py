"""Shared helpers for Magnets modal transform operators."""

from __future__ import annotations

from mathutils import Vector

# Viewport zoom events pass through during the modal. Orbit is excluded: it
# would change the projection plane mid-drag and jump the pointer-to-world map.
_NAV_PASSTHROUGH = {
    "WHEELUPMOUSE",
    "WHEELDOWNMOUSE",
    "WHEELINMOUSE",
    "WHEELOUTMOUSE",
}

_AXIS_KEYS = {"X": 0, "Y": 1, "Z": 2}
_AXIS_NAME = ("X", "Y", "Z")


class AxisConstraint:
    """Single-axis (world) lock toggled with X/Y/Z, like native transform."""

    def __init__(self) -> None:
        self.index: int | None = None

    @property
    def active(self) -> bool:
        """True when an axis lock is engaged."""
        return self.index is not None

    @property
    def name(self) -> str:
        """Locked axis name, or empty when free."""
        return _AXIS_NAME[self.index] if self.index is not None else ""

    def handle_key(self, event) -> bool:
        """Toggle the lock on a fresh X/Y/Z press. Returns True if consumed."""
        if event.value != "PRESS":
            return False
        idx = _AXIS_KEYS.get(event.type)
        if idx is None:
            return False
        self.index = None if self.index == idx else idx
        return True

    def project(self, delta: Vector) -> Vector:
        """Constrain a world-space delta to the locked axis (identity if free)."""
        if self.index is None:
            return delta
        out = Vector((0.0, 0.0, 0.0))
        out[self.index] = delta[self.index]
        return out

    def axis_vector(self) -> Vector | None:
        """Unit world vector for the locked axis, or None."""
        if self.index is None:
            return None
        v = Vector((0.0, 0.0, 0.0))
        v[self.index] = 1.0
        return v


def is_nav_event(event) -> bool:
    """True if the event should pass through for viewport zoom."""
    return event.type in _NAV_PASSTHROUGH


def set_header(context, text: str) -> None:
    """Set the 3D View header text during a modal.

    Args:
        context: Blender context.
        text: Header string.
    """
    area = getattr(context, "area", None)
    if area is not None:
        area.header_text_set(text)


def clear_header(context) -> None:
    """Clear the 3D View header text."""
    area = getattr(context, "area", None)
    if area is not None:
        area.header_text_set(None)
