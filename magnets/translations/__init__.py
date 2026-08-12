"""Add-on UI translations for ``bpy.app.translations``.

English is the source language (msgids in RNA/UI code). Locale modules export
``TRANSLATIONS`` maps keyed by ``(context, msgid)``. Blender selects the active
locale from Preferences → Interface → Translation.
"""

from __future__ import annotations

import bpy

from . import de_DE, es_ES, fr_FR, it_IT, nl_NL

# Locale keys match Blender UI language codes. ``es`` is what Blender reports
# for Spanish; ``es_ES`` is registered as well for country-specific lookups.
translations_dict: dict[str, dict[tuple[str, str], str]] = {
    "fr_FR": fr_FR.TRANSLATIONS,
    "es": es_ES.TRANSLATIONS,
    "es_ES": es_ES.TRANSLATIONS,
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
