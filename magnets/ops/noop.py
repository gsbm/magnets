"""Internal no-op operator for registration and smoke tests."""

import bpy


class MAGNETS_OT_noop(bpy.types.Operator):
    """Internal registration smoke-test operator."""
    bl_idname = "magnets.noop"
    bl_label = "Magnets: No-op"
    bl_description = "Internal Magnets registration smoke-test operator"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        self.report({"INFO"}, "Magnets is installed and registered.")
        return {"FINISHED"}


def register():
    bpy.utils.register_class(MAGNETS_OT_noop)


def unregister():
    bpy.utils.unregister_class(MAGNETS_OT_noop)
