"""Magnets Blender add-on entry point.

Metadata lives in ``blender_manifest.toml``; there is no ``bl_info`` block.
"""

from . import keymaps, ops, preferences, properties, transform_overlay, translations, ui

_modules = (preferences, properties, ops, ui)


def register():
    for mod in _modules:
        mod.register()
    keymaps.register()
    transform_overlay.register()
    translations.register()


def unregister():
    translations.unregister()
    transform_overlay.unregister()
    keymaps.unregister()
    for mod in reversed(_modules):
        mod.unregister()
