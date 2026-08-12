"""Scene-option presets and reset helpers."""

from __future__ import annotations

import bpy

from ..properties import get_options

# Screen-space tolerance profiles (pixels). Keys map to MagnetsOptions fields.
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
        "max_guides": 3,
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


class MAGNETS_OT_options_preset(bpy.types.Operator):
    """Apply a named options preset."""
    bl_idname = "magnets.options_preset"
    bl_label = "Magnets Preset"
    bl_description = "Set snap tolerances to a preset profile"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    preset: bpy.props.EnumProperty(
        name="Preset",
        items=[
            ("PRECISE", "Precise", "Tight tolerances for close work"),
            ("BALANCED", "Balanced", "Default tolerances"),
            ("LOOSE", "Loose", "Wide tolerances for blocking out"),
        ],
        default="BALANCED",
    )

    def execute(self, context):
        """Run a non-modal operator action."""
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
        """Run a non-modal operator action."""
        opts = get_options(context)
        for prop in opts.bl_rna.properties:
            if prop.is_readonly or prop.identifier == "rna_type":
                continue
            opts.property_unset(prop.identifier)
        return {"FINISHED"}


_classes = (MAGNETS_OT_options_preset, MAGNETS_OT_options_reset)


def register():
    """Register Blender classes / handlers for this module."""
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
