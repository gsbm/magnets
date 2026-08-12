"""Keymaps binding G/R/S in the 3D View to Magnets modal operators."""

from __future__ import annotations

import bpy

_addon_keymaps: list = []

# (operator idname, key)
_BINDINGS = (
    ("magnets.translate", "G"),
    ("magnets.rotate", "R"),
    ("magnets.scale", "S"),
)


def register():
    """Register Blender classes / handlers for this module."""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    for idname, key in _BINDINGS:
        kmi = km.keymap_items.new(idname, key, "PRESS")
        _addon_keymaps.append((km, kmi))
    _sync_active()


def _sync_active():
    """Match kmi.active to the current Precision Mode preference."""
    from .preferences import get_prefs

    try:
        active = get_prefs(bpy.context).precision_mode
    except (KeyError, AttributeError):
        active = False
    for _km, kmi in _addon_keymaps:
        kmi.active = active


def set_active(active: bool):
    """Enable or disable Magnets keymap items."""
    for _km, kmi in _addon_keymaps:
        kmi.active = active


def unregister():
    """Unregister Blender classes / handlers for this module."""
    for km, kmi in _addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except (RuntimeError, ReferenceError):
            pass
    _addon_keymaps.clear()
