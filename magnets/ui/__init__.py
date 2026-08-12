"""UI panels."""

from . import panel

_modules = (panel,)


def register():
    """Register Blender classes / handlers for this module."""
    for mod in _modules:
        mod.register()


def unregister():
    """Unregister Blender classes / handlers for this module."""
    for mod in reversed(_modules):
        mod.unregister()
