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
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
