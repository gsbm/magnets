"""Rotate modal operator with angle snap and guide inference."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from ..adapters.extract import object_feature_pool
from ..adapters.snapshot import InteractionSnapshot
from ..core.resolver import snap_angle
from ..core.tolerance import SnapHysteresis
from ..core.transform import TransformMode
from ..draw import handler as draw
from ..properties import extract_options, get_options
from .modal_common import AxisConstraint, clear_header, is_nav_event, set_header
from .pipeline import apply_object_rotation, push_guides, run_inference


class MAGNETS_OT_rotate(bpy.types.Operator):
    """Modal rotate with Magnets guides."""
    bl_idname = "magnets.rotate"
    bl_label = "Magnets Rotate"
    bl_description = "Rotate with Magnets geometric guides"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Return True when the operator can run in ``context``."""
        return (
            context.mode == "OBJECT"
            and context.active_object is not None
            and get_options(context).enabled
            and context.space_data
            and context.space_data.type == "VIEW_3D"
        )

    def invoke(self, context, event):
        """Begin the operator and enter modal if needed.

        Args:
            context: Blender context.
            event: Invoking event.

        Returns:
            Blender operator return set.
        """
        self.obj = context.active_object
        self.region = context.region
        self.rv3d = context.region_data
        self.init_matrix = self.obj.matrix_world.copy()
        self.pivot = self.init_matrix.translation.copy()
        self._snap = SnapHysteresis()
        self._axis = AxisConstraint()
        opts = get_options(context)

        # Native R rotates around the axis pointing at the viewer.
        self._view_axis = (self.rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))).normalized()

        self.start_x = event.mouse_region_x

        self._snapshot = InteractionSnapshot.from_context(
            context,
            exclude=[self.obj],
            surfaces=opts.enable_tangency,
            **extract_options(opts),
        )

        draw.enable()
        context.window_manager.modal_handler_add(self)
        self._update(context, event)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        """Handle a modal event.

        Args:
            context: Blender context.
            event: Current event.

        Returns:
            Blender operator return set.
        """
        if is_nav_event(event):
            return {"PASS_THROUGH"}

        if self._axis.handle_key(event):
            self._update(context, event)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            self._update(context, event)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}:
            return self._finish(context)

        if event.type in {"RIGHTMOUSE", "ESC"}:
            return self._cancel(context)

        return {"RUNNING_MODAL"}

    def _axis_vector(self) -> Vector:
        locked = self._axis.axis_vector()
        return locked if locked is not None else self._view_axis

    def _update(self, context, event):
        opts = get_options(context)
        dx = event.mouse_region_x - self.start_x
        angle = dx * 0.01

        increment = opts.angle_snap_increment
        if increment > 0.0:
            angle = snap_angle(angle, increment)

        axis = self._axis_vector()
        self.obj.matrix_world = self.init_matrix.copy()
        apply_object_rotation(self.obj, axis, angle, self.pivot)

        moving = object_feature_pool(self.obj, **extract_options(opts))
        anchor = self.obj.matrix_world.translation.copy()

        result = run_inference(
            context,
            region=self.region,
            rv3d=self.rv3d,
            snapshot=self._snapshot,
            moving=moving,
            anchor_world=anchor,
            snap=self._snap,
            transform_mode=TransformMode.ROTATE,
        )

        if result.snapped and abs(result.rotation_angle) > 1e-9:
            self.obj.matrix_world = self.init_matrix.copy()
            apply_object_rotation(
                self.obj, result.rotation_axis, result.rotation_angle, self.pivot
            )

        push_guides(
            context,
            region=self.region,
            rv3d=self.rv3d,
            result=result,
            depth_co=self.obj.matrix_world.translation,
        )
        self._set_header(context, angle, result)

    def _set_header(self, context, angle, result):
        which = f" [{self._axis.name}]" if self._axis.active else " [view]"
        snap = "  ·  snapped" if result.snapped else ""
        set_header(
            context,
            f"Magnets Rotate{which}: {math.degrees(angle):.1f}deg"
            f"   (X/Y/Z lock axis){snap}",
        )

    def _finish(self, context):
        draw.disable()
        clear_header(context)
        context.area.tag_redraw()
        return {"FINISHED"}

    def _cancel(self, context):
        self.obj.matrix_world = self.init_matrix
        draw.disable()
        clear_header(context)
        context.area.tag_redraw()
        return {"CANCELLED"}


def register():
    """Register Blender classes / handlers for this module."""
    bpy.utils.register_class(MAGNETS_OT_rotate)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    bpy.utils.unregister_class(MAGNETS_OT_rotate)
