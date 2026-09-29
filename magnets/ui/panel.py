"""Sidebar panels for Magnets scene options."""

import bpy

from ..core.families import FAMILIES
from ..core.frames import Frame
from ..ops.presets import matching_preset
from ..preferences import get_prefs
from ..properties import get_options
from ..translations import CONTEXT

_PRESET_BUTTONS = (
    ("PRECISE", "Precise"),
    ("BALANCED", "Balanced"),
    ("LOOSE", "Loose"),
)


def _draw_essentials(layout, context, opts):
    """Presets and snap timing: shared by the sidebar and popover."""
    current = matching_preset(opts)
    row = layout.row(align=True)
    row.label(text="", icon="PRESET")
    for preset, text in _PRESET_BUTTONS:
        op = row.operator(
            "magnets.options_preset", text=text, depress=current == preset
        )
        op.preset = preset
    row.separator()
    row.operator("magnets.options_reset", text="", icon="LOOP_BACK")

    layout.row().prop(get_prefs(context), "snap_timing", expand=True)


class MAGNETS_PT_header_popover(bpy.types.Panel):
    """Compact settings popover opened from the 3D Viewport header.

    Deliberately flat (no child panels): drawing a panel with sub-panels as a
    popover crashed Blender 5.2 inside ``Layout::panel_prop``.
    """
    bl_label = "Magnets"
    bl_idname = "MAGNETS_PT_header_popover"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_ui_units_x = 13

    def draw(self, context):
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(opts, "enabled")
        body = layout.column()
        body.active = opts.enabled
        _draw_essentials(body, context, opts)

        col = body.column(align=True)
        col.prop(opts, "snap_tolerance_px")
        col.prop(opts, "angle_snap_increment")
        body.prop(opts, "show_passive_guides")
        col = body.column(heading="Blender Snap")
        col.prop(opts, "defer_to_native_snap", text="Yield")
        body.label(text="More options in the sidebar (N)", icon="MENU_PANEL")


class MAGNETS_PT_panel(bpy.types.Panel):
    """Root Magnets N-panel."""
    bl_label = "Magnets"
    bl_idname = "MAGNETS_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"

    def draw_header(self, context):
        self.layout.prop(get_options(context), "enabled", text="")

    def draw(self, context):
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = opts.enabled
        _draw_essentials(layout, context, opts)


class MAGNETS_PT_snapping(bpy.types.Panel):
    """Snapping tolerance sub-panel."""
    bl_label = "Snapping"
    bl_translation_context = CONTEXT
    bl_idname = "MAGNETS_PT_snapping"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"
    bl_parent_id = "MAGNETS_PT_panel"

    def draw(self, context):
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
        layout.prop(opts, "depth_axis_cutoff")
        layout.prop(opts, "prioritize_nearby")

        col = layout.column(heading="Blender Snap")
        col.prop(opts, "defer_to_native_snap", text="Yield")
        if opts.defer_to_native_snap and context.scene.tool_settings.use_snap:
            layout.label(text="Blender snapping takes over", icon="SNAP_ON")


class MAGNETS_PT_guides(bpy.types.Panel):
    """Guide display sub-panel."""
    bl_label = "Guides"
    bl_idname = "MAGNETS_PT_guides"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Magnets"
    bl_parent_id = "MAGNETS_PT_panel"

    def draw(self, context):
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
        col.prop(opts, "show_guide_labels", text="Labels")
        sub = col.column()
        sub.active = opts.show_guide_labels
        sub.prop(opts, "show_feature_hints", text="Feature Hints")

        col = layout.column()
        # Proximity fade is a per-user display setting, stored in preferences.
        col.prop(get_prefs(context), "guide_fade_passive")
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
        opts = get_options(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = opts.enabled

        layout.prop(opts, "alignment_frame", text="Frame")
        if opts.alignment_frame == Frame.CUSTOM.value:
            layout.prop(opts, "custom_frame_object", text="Object")

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
        opts = get_options(context)
        layout = self.layout
        layout.active = opts.enabled
        grid = layout.grid_flow(columns=2, even_columns=True)
        for fid, _label in FAMILIES:
            grid.prop(opts, f"enable_{fid}")
        layout.prop(opts, "allow_diagonal_guides")


def draw_view3d_header(self, context):
    """Magnets on/off button + settings popover in the 3D Viewport header.

    The button is an operator (not the raw property) so its tooltip shows the
    shortcut and right-click offers Assign / Change Shortcut.
    """
    try:
        if not get_prefs(context).show_header_toggle:
            return
    except KeyError:
        return
    opts = get_options(context)
    row = self.layout.row(align=True)
    row.operator(
        "magnets.toggle", text="", icon="FORCE_MAGNETIC", depress=opts.enabled
    )
    sub = row.row(align=True)
    sub.active = opts.enabled
    sub.popover(panel=MAGNETS_PT_header_popover.bl_idname, text="")


_CLASSES = (
    MAGNETS_PT_header_popover,
    MAGNETS_PT_panel,
    MAGNETS_PT_snapping,
    MAGNETS_PT_guides,
    MAGNETS_PT_alignment,
    MAGNETS_PT_families,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_header.append(draw_view3d_header)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_view3d_header)
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
