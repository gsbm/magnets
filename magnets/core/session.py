"""Transform session selection guards (no bpy)."""


def selection_matches_session(
    session_moving: frozenset[str],
    session_edit: bool,
    *,
    edit_mode: bool,
    selected_names: frozenset[str],
    active_name: str | None,
) -> bool:
    """Return True while the transformed objects are still the active selection."""
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
    """Return True when Blender's own snapping governs the transform.

    Magnets then yields so the two snaps never fight. ``op_snap`` is the
    finished operator's ``snap`` flag (it records a held Ctrl toggle), or None
    mid-drag.
    """
    return bool(tool_use_snap) or bool(op_snap)
