"""Canonical marker-family ids and labels.

Family ids are stable preference keys (``enable_<id>``) and solver registry keys.
"""

from .transform import TransformMode

# (id, human-readable label).
FAMILIES: tuple[tuple[str, str], ...] = (
    ("alignment", "Alignment"),
    ("spacing", "Equal Spacing"),
    ("repeat_size", "Repeat Size"),
    ("equal_size", "Equal Size"),
    ("midpoint", "Midpoint"),
    # Id kept for saved settings; it also gates the surface (BVH) sampling.
    ("tangency", "Surface Contact"),
    ("sphere_tangency", "Sphere Tangency"),
    ("parallel", "Parallel"),
    ("collinear", "Collinear"),
    ("coplanar", "Coplanar"),
    ("concentric", "Concentric"),
    ("symmetry", "Symmetry"),
)

FAMILY_IDS: tuple[str, ...] = tuple(fid for fid, _label in FAMILIES)

# Less-used families, off until the user enables them in Guide Types: a plain
# align or distribute should not meet them.
DEFAULT_OFF: frozenset[str] = frozenset(
    ("repeat_size", "sphere_tangency", "symmetry", "collinear", "concentric")
)

# Families whose result the action can actually apply. Every solver emits a
# translation, except equal size (a scale factor). Rotate snaps to angle
# increments outside the solvers, so no solver guide runs while rotating.
_ROTATE_FAMILIES: frozenset[str] = frozenset()
_SCALE_FAMILIES = frozenset(("equal_size",))
_TRANSLATE_EXCLUDED = frozenset(("equal_size",))


def is_family(family_id: str) -> bool:
    """Return True if ``family_id`` is a known marker family."""
    return family_id in FAMILY_IDS


def families_for_mode(mode, enabled: set[str]) -> set[str]:
    """The enabled families that can act in ``mode`` (Extrude moves too)."""
    if mode == TransformMode.ROTATE:
        return enabled & _ROTATE_FAMILIES
    if mode == TransformMode.SCALE:
        return enabled & _SCALE_FAMILIES
    return enabled - _TRANSLATE_EXCLUDED
