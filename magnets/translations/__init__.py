"""Add-on UI translations for ``bpy.app.translations``.

English is the source language (msgids in RNA/UI code). Locale modules export
``TRANSLATIONS`` maps keyed by ``(context, msgid)``. Blender selects the active
locale from Preferences → Interface → Translation.
"""

from __future__ import annotations

import bpy

from . import de_DE, es, fr_FR, it_IT, nl_NL

# Translation context for short msgids that Blender's own catalogue already
# translates with an unrelated meaning ("Frame" is an animation frame there).
# Blender's catalogue wins over add-on catalogues for a shared (context, msgid).
CONTEXT = "Magnets"

# Keys and module names match Blender's UI language codes
# (``bpy.app.translations.locales``); Spanish is ``es``.
translations_dict: dict[str, dict[tuple[str, str], str]] = {
    "fr_FR": fr_FR.TRANSLATIONS,
    "es": es.TRANSLATIONS,
    "it_IT": it_IT.TRANSLATIONS,
    "de_DE": de_DE.TRANSLATIONS,
    "nl_NL": nl_NL.TRANSLATIONS,
}


def register():
    """Register translation catalogs with Blender."""
    bpy.app.translations.register(__package__, translations_dict)


def unregister():
    """Unregister translation catalogs from Blender."""
    bpy.app.translations.unregister(__package__)
