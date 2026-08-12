"""Modal transform operators."""

from . import (
    modal_mesh_ops,
    modal_rotate,
    modal_scale,
    modal_translate,
    noop,
    presets,
)

_modules = (noop, modal_translate, modal_rotate, modal_scale, modal_mesh_ops, presets)


def register():
    """Register Blender classes / handlers for this module."""
    for mod in _modules:
        mod.register()


def unregister():
    """Unregister Blender classes / handlers for this module."""
    for mod in reversed(_modules):
        mod.unregister()
