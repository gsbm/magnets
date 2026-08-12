"""Magnets Blender add-on entry point.

Metadata is declared in ``blender_manifest.toml`` (Blender 4.2+ Extensions);
there is no ``bl_info`` block.

Registration order: preferences → operators → UI → keymaps → translations.
"""

from . import keymaps, ops, preferences, properties, transform_overlay, translations, ui

_modules = (preferences, properties, ops, ui)


def register():
    """Register Blender classes / handlers for this module."""
    for mod in _modules:
        mod.register()
    keymaps.register()
    transform_overlay.register()
    translations.register()


def unregister():
    """Unregister Blender classes / handlers for this module."""
    translations.unregister()
    transform_overlay.unregister()
    keymaps.unregister()
    for mod in reversed(_modules):
        mod.unregister()
