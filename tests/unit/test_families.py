"""Sanity checks for the shared marker-family registry."""

from core import families


def test_eleven_families():
    # Repeat Size was split out of Equal Spacing; Perpendicular was removed
    # (compared in 3D it held for any box, and nothing could apply it).
    assert len(families.FAMILIES) == 11


def test_less_used_families_default_off():
    assert families.DEFAULT_OFF == {"repeat_size", "symmetry", "collinear", "concentric"}
    assert families.DEFAULT_OFF <= set(families.FAMILY_IDS)


def test_ids_unique_and_slug_like():
    ids = families.FAMILY_IDS
    assert len(set(ids)) == len(ids), "family ids must be unique"
    for fid in ids:
        assert fid.islower()
        assert " " not in fid


def test_is_family():
    assert families.is_family("alignment")
    assert not families.is_family("nope")


def test_labels_present():
    for fid, label in families.FAMILIES:
        assert fid and label
