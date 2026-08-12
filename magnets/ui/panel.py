"""Sidebar panels for Magnets scene options."""

import bpy

from ..core.families import FAMILIES
from ..core.frames import Frame
from ..properties import get_options


class MAGNETS_PT_panel(bpy.types.Panel):
    """Root Magnets N-panel."""
    bl_label = "Magnets"
    bl_idname = "MAGNETS_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"

    def draw_header(self, context):
        """Draw the panel header row."""
        self.layout.prop(get_options(context), "enabled", text="")

    def draw(self, context):
        """Draw UI controls into ``layout``."""
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = opts.enabled
        layout.prop(opts, "soft_snap")

        row = layout.row(align=True)
        row.label(text="Presets")
        row.operator("magnets.options_preset", text="Precise").preset = "PRECISE"
        row.operator("magnets.options_preset", text="Balanced").preset = "BALANCED"
        row.operator("magnets.options_preset", text="Loose").preset = "LOOSE"
        row.separator()
        row.operator("magnets.options_reset", text="", icon="LOOP_BACK")


class MAGNETS_PT_snapping(bpy.types.Panel):
    """Snapping tolerance sub-panel."""
    bl_label = "Snapping"
    bl_idname = "MAGNETS_PT_snapping"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"
    bl_parent_id = "MAGNETS_PT_panel"

    def draw(self, context):
        """Draw UI controls into ``layout``."""
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = opts.enabled

        col = layout.column(align=True)
        col.prop(opts, "snap_tolerance_px")
        col.prop(opts, "snap_release_hysteresis_px")
        col.prop(opts, "snap_reengage_margin_px")
        layout.prop(opts, "angle_snap_increment")
        layout.prop(opts, "spacing_metric")


class MAGNETS_PT_guides(bpy.types.Panel):
    """Guide display sub-panel."""
    bl_label = "Guides"
    bl_idname = "MAGNETS_PT_guides"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"
    bl_parent_id = "MAGNETS_PT_panel"

    def draw(self, context):
        """Draw UI controls into ``layout``."""
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = opts.enabled

        col = layout.column(align=True)
        col.prop(opts, "passive_range_px")
        col.prop(opts, "max_guides")
        col.prop(opts, "nms_distance_px")

        col = layout.column(heading="Show")
        col.prop(opts, "show_passive_guides", text="Passive Guides")
        col.prop(opts, "show_guide_ticks", text="Ticks")
        col.prop(opts, "show_feature_hints", text="Feature Hints")

        col = layout.column()
        col.prop(opts, "guide_fade_passive")
        col.prop(opts, "extend_guides_to_viewport")


class MAGNETS_PT_alignment(bpy.types.Panel):
    """Alignment-axis sub-panel."""
    bl_label = "Alignment"
    bl_idname = "MAGNETS_PT_alignment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"
    bl_parent_id = "MAGNETS_PT_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        """Draw UI controls into ``layout``."""
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = opts.enabled

        layout.prop(opts, "alignment_frame", text="Frame")
        if opts.alignment_frame == Frame.CUSTOM.value:
            layout.prop(opts, "custom_frame_object_name", text="Object")

        row = layout.row(heading="Axes")
        row.prop(opts, "snap_axis_x", text="X", toggle=True)
        row.prop(opts, "snap_axis_y", text="Y", toggle=True)
        row.prop(opts, "snap_axis_z", text="Z", toggle=True)

        col = layout.column(heading="Reference Points")
        col.prop(opts, "align_use_origin", text="Origin")
        col.prop(opts, "align_use_pivot", text="Pivot")
        col.prop(opts, "align_use_centroid", text="Centroid")
        col.prop(opts, "align_use_face_centers", text="Face Centers")
        col.prop(opts, "align_use_corners", text="Bounding Box Corners")


class MAGNETS_PT_families(bpy.types.Panel):
    """Constraint-family toggles sub-panel."""
    bl_label = "Guide Types"
    bl_idname = "MAGNETS_PT_families"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"
    bl_parent_id = "MAGNETS_PT_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        """Draw UI controls into ``layout``."""
        opts = get_options(context)
        layout = self.layout
        layout.active = opts.enabled
        grid = layout.grid_flow(columns=2, even_columns=True)
        for fid, _label in FAMILIES:
            grid.prop(opts, f"enable_{fid}")


_CLASSES = (
    MAGNETS_PT_panel,
    MAGNETS_PT_snapping,
    MAGNETS_PT_guides,
    MAGNETS_PT_alignment,
    MAGNETS_PT_families,
)


def register():
    """Register Blender classes / handlers for this module."""
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
