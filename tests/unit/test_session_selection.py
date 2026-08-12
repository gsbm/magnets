"""Selection guards for transform overlay sessions."""

from core.session import selection_matches_session


def test_selection_matches_object_mode_while_moving_still_selected():
    session = frozenset({"Cube"})
    assert selection_matches_session(
        session,
        False,
        edit_mode=False,
        selected_names=frozenset({"Cube"}),
        active_name="Cube",
    )


def test_selection_invalid_when_moving_object_deselected():
    session = frozenset({"Cube"})
    assert not selection_matches_session(
        session,
        False,
        edit_mode=False,
        selected_names=frozenset(),
        active_name=None,
    )


def test_selection_invalid_when_another_object_selected_instead():
    session = frozenset({"Cube"})
    assert not selection_matches_session(
        session,
        False,
        edit_mode=False,
        selected_names=frozenset({"Sphere"}),
        active_name="Sphere",
    )


def test_selection_invalid_when_active_is_not_among_moving_objects():
    session = frozenset({"Cube"})
    assert not selection_matches_session(
        session,
        False,
        edit_mode=False,
        selected_names=frozenset({"Cube", "Sphere"}),
        active_name="Sphere",
    )


def test_selection_allows_multi_select_when_all_moving_still_selected():
    session = frozenset({"Cube", "Sphere"})
    assert selection_matches_session(
        session,
        False,
        edit_mode=False,
        selected_names=frozenset({"Cube", "Sphere", "Empty"}),
        active_name="Cube",
    )


def test_selection_invalid_when_one_moving_object_removed_from_selection():
    session = frozenset({"Cube", "Sphere"})
    assert not selection_matches_session(
        session,
        False,
        edit_mode=False,
        selected_names=frozenset({"Cube"}),
        active_name="Cube",
    )


def test_selection_edit_mode_requires_same_active_mesh():
    session = frozenset({"Cube"})
    assert selection_matches_session(
        session,
        True,
        edit_mode=True,
        selected_names=frozenset({"Cube"}),
        active_name="Cube",
    )
    assert not selection_matches_session(
        session,
        True,
        edit_mode=False,
        selected_names=frozenset({"Cube"}),
        active_name="Cube",
    )
