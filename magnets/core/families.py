"""Canonical marker-family ids and labels.

Family ids are stable preference keys (``enable_<id>``) and solver registry keys.
"""

# (id, human-readable label).
FAMILIES: tuple[tuple[str, str], ...] = (
    ("alignment", "Alignment"),
    ("spacing", "Equal Spacing"),
    ("equal_size", "Equal Size"),
    ("midpoint", "Midpoint"),
    ("tangency", "Tangency"),
    ("parallel", "Parallel"),
    ("perpendicular", "Perpendicular"),
    ("collinear", "Collinear"),
    ("coplanar", "Coplanar"),
    ("concentric", "Concentric"),
    ("symmetry", "Symmetry"),
)

FAMILY_IDS: tuple[str, ...] = tuple(fid for fid, _label in FAMILIES)


def is_family(family_id: str) -> bool:
    """Return True if ``family_id`` is a known marker family."""
    return family_id in FAMILY_IDS
