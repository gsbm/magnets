"""Internal no-op operator for registration and smoke tests."""

import bpy


class MAGNETS_OT_noop(bpy.types.Operator):
    """Internal registration smoke-test operator."""
    bl_idname = "magnets.noop"
    bl_label = "Magnets: No-op"
    bl_description = "Internal Magnets registration smoke-test operator"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        """Run a non-modal operator action."""
        self.report({"INFO"}, "Magnets is installed and registered.")
        return {"FINISHED"}


def register():
    """Register Blender classes / handlers for this module."""
    bpy.utils.register_class(MAGNETS_OT_noop)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    bpy.utils.unregister_class(MAGNETS_OT_noop)
