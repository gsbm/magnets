"""Sanity checks for the shared marker-family registry."""

from core import families


def test_eleven_families():
    # The spec defines exactly 11 core marker families.
    assert len(families.FAMILIES) == 11


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
