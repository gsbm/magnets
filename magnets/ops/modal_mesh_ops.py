"""Edit-mode mesh ops that hand off to Magnets translate."""

from __future__ import annotations

import bpy


class _MagnetsMeshOpBase:
    """Invoke a native mesh op then hand off to Magnets translate."""

    native_op: str = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "EDIT_MESH"
            and context.active_object is not None
            and context.space_data
            and context.space_data.type == "VIEW_3D"
        )

    def execute(self, context):
        op = getattr(bpy.ops, self.native_op.split(".")[0])
        mesh_op = getattr(op, self.native_op.split(".")[1])
        if not mesh_op.poll():
            self.report({"WARNING"}, f"{self.native_op} unavailable")
            return {"CANCELLED"}
        return mesh_op("EXEC_DEFAULT")

    def invoke(self, context, event):
        """Run the operator, then enter modal if needed."""
        res = self.execute(context)
        if res != {"FINISHED"}:
            return res
        return bpy.ops.magnets.translate("INVOKE_DEFAULT")


class MAGNETS_OT_extrude(_MagnetsMeshOpBase, bpy.types.Operator):
    """Extrude then Magnets translate."""
    bl_idname = "magnets.extrude"
    bl_label = "Magnets Extrude"
    bl_description = "Extrude region then move with Magnets guides"
    native_op = "mesh.extrude_region"


class MAGNETS_OT_bevel(_MagnetsMeshOpBase, bpy.types.Operator):
    """Bevel then Magnets translate."""
    bl_idname = "magnets.bevel"
    bl_label = "Magnets Bevel"
    bl_description = "Bevel then adjust with Magnets guides"
    native_op = "mesh.bevel"


class MAGNETS_OT_inset(_MagnetsMeshOpBase, bpy.types.Operator):
    """Inset then Magnets translate."""
    bl_idname = "magnets.inset"
    bl_label = "Magnets Inset"
    bl_description = "Inset faces then move with Magnets guides"
    native_op = "mesh.inset"


class MAGNETS_OT_knife(_MagnetsMeshOpBase, bpy.types.Operator):
    """Knife then Magnets translate."""
    bl_idname = "magnets.knife"
    bl_label = "Magnets Knife"
    bl_description = "Knife project cut then move with Magnets guides"
    native_op = "mesh.knife_project"


_CLASSES = (
    MAGNETS_OT_extrude,
    MAGNETS_OT_bevel,
    MAGNETS_OT_inset,
    MAGNETS_OT_knife,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
