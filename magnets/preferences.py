"""Add-on preferences (Edit → Preferences → Extensions)."""

import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, IntProperty


def _update_precision_mode(self, context):
    from . import keymaps

    keymaps.set_active(self.precision_mode)


def _update_debug(self, context):
    from . import log

    log.set_debug(self.debug)


class MagnetsPreferences(bpy.types.AddonPreferences):
    """Add-on preferences panel."""
    bl_idname = __package__

    # ── Transform behaviour ────────────────────────────────────────────────────
    precision_mode: BoolProperty(
        name="Precision Mode",
        description=(
            "Bind G / R / S to the Magnets modal operators, which lock onto a "
            "guide while dragging. Leave off to use Blender's native transform, "
            "which snaps to the engaged guide when released"
        ),
        default=False,
        update=_update_precision_mode,
    )
    debug: BoolProperty(
        name="Debug Logging",
        description="Log Magnets diagnostics to the system console "
        "(Window ▸ Toggle System Console)",
        default=False,
        update=_update_debug,
    )

    # ── Guide colors ───────────────────────────────────────────────────────────
    guide_color_passive: FloatVectorProperty(
        name="Passive Color",
        description="Guide color while approaching the snap zone",
        subtype="COLOR",
        size=4,
        default=(1.0, 0.031, 0.219, 0.70),
        min=0.0,
        max=1.0,
    )
    guide_color_active: FloatVectorProperty(
        name="Active Color",
        description="Guide color while engaged",
        subtype="COLOR",
        size=4,
        default=(1.0, 0.012, 0.141, 1.0),
        min=0.0,
        max=1.0,
    )

    # ── Line style ─────────────────────────────────────────────────────────────
    guide_line_width: FloatProperty(
        name="Line Width",
        description="Guide line width in pixels",
        default=1.0,
        min=0.5,
        max=4.0,
        subtype="PIXEL",
    )
    guide_solid_lines: BoolProperty(
        name="Solid Lines",
        description="Draw solid guide lines, otherwise dashed",
        default=True,
    )

    # ── Proximity fade ─────────────────────────────────────────────────────────
    guide_fade_passive: BoolProperty(
        name="Proximity Fade",
        description="Fade guide opacity in as the cursor approaches the snap zone",
        default=True,
    )

    # ── Snap dot ───────────────────────────────────────────────────────────────
    show_snap_dot: BoolProperty(
        name="Snap Anchor Dot",
        description="Draw a dot at the coincident point when a guide is engaged",
        default=True,
    )
    snap_dot_radius_px: IntProperty(
        name="Dot Radius",
        description="Radius of the snap anchor dot in pixels",
        default=4,
        min=1,
        max=12,
        subtype="PIXEL",
    )

    # ── Intersection dot ───────────────────────────────────────────────────────
    show_intersection_dot: BoolProperty(
        name="Intersection Dot",
        description="Draw a marker where two engaged guides cross",
        default=True,
    )

    # ── Active pulse ───────────────────────────────────────────────────────────
    guide_active_pulse: BoolProperty(
        name="Snap Pulse",
        description="Brief brightness flash at the moment a guide engages",
        default=True,
    )

    def draw(self, context):
        """Draw UI controls into ``layout``."""
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "precision_mode")
        layout.prop(self, "debug")

        col = layout.column()
        col.prop(self, "guide_color_passive")
        col.prop(self, "guide_color_active")
        col.prop(self, "guide_line_width")
        col.prop(self, "guide_solid_lines")

        col = layout.column(heading="Indicators")
        col.prop(self, "guide_fade_passive")
        col.prop(self, "guide_active_pulse")
        col.prop(self, "show_intersection_dot")

        col = layout.column(heading="Snap Anchor Dot")
        col.prop(self, "show_snap_dot", text="")
        sub = col.row()
        sub.active = self.show_snap_dot
        sub.prop(self, "snap_dot_radius_px")


def get_prefs(context) -> "MagnetsPreferences":
    """Return add-on preferences (colours + visual settings).

    Works for both legacy (bl_info) and Extensions installs.
    """
    addons = context.preferences.addons
    pkg = __package__
    if pkg in addons:
        return addons[pkg].preferences
    for key, entry in addons.items():
        if key == "magnets" or key.endswith(".magnets"):
            return entry.preferences
    raise KeyError(
        f"Magnets preferences not found (package={pkg!r}). "
        "Enable the Magnets extension in Edit → Preferences → Extensions."
    )


classes = (MagnetsPreferences,)


def register():
    """Register Blender classes / handlers for this module."""
    for cls in classes:
        bpy.utils.register_class(cls)
    # Honour a saved Debug Logging preference at startup (the update callback
    # only fires on change).
    from . import log

    try:
        log.set_debug(bool(get_prefs(bpy.context).debug))
    except Exception:  # pragma: no cover - prefs not ready during some reloads
        pass


def unregister():
    """Unregister Blender classes / handlers for this module."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
