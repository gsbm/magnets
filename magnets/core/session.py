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
    return active_name is None or active_name in session_moving


def native_snap_in_effect(tool_use_snap: bool, op_snap: bool | None) -> bool:
    """True when Blender's own snapping governs the transform.

    Magnets yields in that case so the two snaps never fight (native snaps to
    a vertex, then Magnets drags it off on release).

    Args:
        tool_use_snap: The scene's ``tool_settings.use_snap`` toggle.
        op_snap: The finished transform's saved ``snap`` flag, which also
            records a held Ctrl snap toggle; None when unreadable (mid-drag).

    Returns:
        Whether native snapping is (or may be) active.
    """
    return bool(tool_use_snap) or bool(op_snap)
