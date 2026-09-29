"""Scene-option presets and reset helpers."""

from __future__ import annotations

import bpy

from ..properties import get_options
from ..translations import CONTEXT

# Screen-space tolerance profiles (pixels). Keys map to MagnetsOptions fields.
# BALANCED must equal the property defaults (checked by the integration suite).
_PRESETS = {
    "PRECISE": {
        "snap_tolerance_px": 8,
        "snap_release_hysteresis_px": 24,
        "snap_reengage_margin_px": 8,
        "passive_range_px": 48,
        "nms_distance_px": 18,
        "max_guides": 4,
    },
    "BALANCED": {
        "snap_tolerance_px": 16,
        "snap_release_hysteresis_px": 40,
        "snap_reengage_margin_px": 12,
        "passive_range_px": 72,
        "nms_distance_px": 24,
        "max_guides": 5,
    },
    "LOOSE": {
        "snap_tolerance_px": 24,
        "snap_release_hysteresis_px": 56,
        "snap_reengage_margin_px": 16,
        "passive_range_px": 110,
        "nms_distance_px": 32,
        "max_guides": 2,
    },
}


def matching_preset(options) -> str | None:
    """Name of the preset the current options equal, or None if customised."""
    for name, values in _PRESETS.items():
        if all(getattr(options, key) == value for key, value in values.items()):
            return name
    return None


class MAGNETS_OT_options_preset(bpy.types.Operator):
    """Apply a named options preset."""
    bl_idname = "magnets.options_preset"
    bl_label = "Magnets Preset"
    bl_description = "Set snap tolerances to a preset profile"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    preset: bpy.props.EnumProperty(
        name="Preset",
        translation_context=CONTEXT,
        items=[
            ("PRECISE", "Precise", "Tight tolerances for close work"),
            ("BALANCED", "Balanced", "Default tolerances"),
            ("LOOSE", "Loose", "Wide tolerances for blocking out"),
        ],
        default="BALANCED",
    )

    def execute(self, context):
        opts = get_options(context)
        for field, value in _PRESETS[self.preset].items():
            setattr(opts, field, value)
        return {"FINISHED"}


class MAGNETS_OT_options_reset(bpy.types.Operator):
    """Reset scene Magnets options."""
    bl_idname = "magnets.options_reset"
    bl_label = "Reset Magnets Options"
    bl_description = "Reset all Magnets scene options to their defaults"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        opts = get_options(context)
        for prop in opts.bl_rna.properties:
            if prop.is_readonly or prop.identifier == "rna_type":
                continue
            opts.property_unset(prop.identifier)
        return {"FINISHED"}


class MAGNETS_OT_toggle(bpy.types.Operator):
    """Turn Magnets guides and snapping on or off for this scene."""
    bl_idname = "magnets.toggle"
    bl_label = "Toggle Magnets"
    bl_description = "Turn Magnets guides and snapping on or off"
    bl_options = {"REGISTER"}

    def execute(self, context):
        opts = get_options(context)
        opts.enabled = not opts.enabled
        # Reports are not translated automatically; pgettext_rpt is Blender 4.0+.
        translations = bpy.app.translations
        rpt = getattr(translations, "pgettext_rpt", translations.pgettext_tip)
        self.report({"INFO"}, rpt("Magnets on" if opts.enabled else "Magnets off"))
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
        return {"FINISHED"}


_classes = (MAGNETS_OT_options_preset, MAGNETS_OT_options_reset, MAGNETS_OT_toggle)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
