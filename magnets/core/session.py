"""Transform session selection guards (no bpy)."""


def selection_matches_session(
    session_moving: frozenset[str],
    session_edit: bool,
    *,
    edit_mode: bool,
    selected_names: frozenset[str],
    active_name: str | None,
) -> bool:
    """True while the objects being transformed are still the active selection.

    Args:
        session_moving: Entity names captured at session start.
        session_edit: Whether the session began in Edit Mode.
        edit_mode: Current Edit Mode flag.
        selected_names: Currently selected object names.
        active_name: Active object name, if any.

    Returns:
        Whether the session selection is still valid.
    """
    if session_edit != edit_mode:
        return False
    if not session_moving:
        return False
    if edit_mode:
        return active_name is not None and active_name in session_moving
    if not selected_names:
        return False
    if not session_moving <= selected_names:
        return False
    if active_name is not None and active_name not in session_moving:
        return False
    return True
