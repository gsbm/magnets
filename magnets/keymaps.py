"""Keymaps for the 3D View.

Two groups:

- Precision Mode items bind G/R/S to Magnets modal operators; they are only
  active while the preference is on.
- The on/off toggle (Shift+Alt+M, unused in Blender's default keymap) is always
  active and can be rebound in the add-on preferences.
"""

from __future__ import annotations

import bpy

_addon_keymaps: list = []
_toggle_keymaps: list = []

# (operator idname, key)
_BINDINGS = (
    ("magnets.translate", "G"),
    ("magnets.rotate", "R"),
    ("magnets.scale", "S"),
)

TOGGLE_IDNAME = "magnets.toggle"
_TOGGLE_KEY = {"type": "M", "value": "PRESS", "shift": True, "alt": True}


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    for idname, key in _BINDINGS:
        kmi = km.keymap_items.new(idname, key, "PRESS")
        _addon_keymaps.append((km, kmi))
    _sync_active()

    kmi = km.keymap_items.new(TOGGLE_IDNAME, **_TOGGLE_KEY)
    _toggle_keymaps.append((km, kmi))


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
    """Enable or disable the Precision Mode keymap items."""
    for _km, kmi in _addon_keymaps:
        kmi.active = active


def draw_toggle_keymap(context, layout):
    """Draw the rebindable on/off shortcut (user keyconfig) in preferences."""
    import rna_keymap_ui

    kc = context.window_manager.keyconfigs.user
    km = kc.keymaps.get("3D View") if kc is not None else None
    if km is None:
        return
    col = layout.column()
    col.label(text="Shortcut")
    for kmi in km.keymap_items:
        if kmi.idname == TOGGLE_IDNAME:
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
            return


def unregister():
    for km, kmi in _addon_keymaps + _toggle_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except (RuntimeError, ReferenceError):
            pass
    _addon_keymaps.clear()
    _toggle_keymaps.clear()
