"""Scale modal operator with equal-size snap."""

from __future__ import annotations

import bpy
from mathutils import Vector

from ..adapters.extract import object_feature_pool
from ..adapters.snapshot import InteractionSnapshot
from ..core.tolerance import SnapHysteresis
from ..core.transform import TransformMode
from ..draw import handler as draw
from ..properties import extract_options, get_options
from .modal_common import (
    AxisConstraint,
    clear_header,
    header_text,
    is_nav_event,
    set_header,
)
from .pipeline import apply_object_scale, push_guides, run_inference


class MAGNETS_OT_scale(bpy.types.Operator):
    """Modal scale with Magnets guides."""
    bl_idname = "magnets.scale"
    bl_label = "Magnets Scale"
    bl_description = "Scale with Magnets geometric guides"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and context.active_object is not None
            and get_options(context).enabled
            and context.space_data
            and context.space_data.type == "VIEW_3D"
        )

    def invoke(self, context, event):
        self.obj = context.active_object
        self.region = context.region
        self.rv3d = context.region_data
        self.init_scale = self.obj.scale.copy()
        self.init_matrix = self.obj.matrix_world.copy()
        self.pivot = self.init_matrix.translation.copy()
        self._snap = SnapHysteresis()
        self._axis = AxisConstraint()
        opts = get_options(context)

        self.start_y = event.mouse_region_y

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

    def _factor_vector(self, factor: float) -> Vector:
        if self._axis.active:
            v = Vector((1.0, 1.0, 1.0))
            v[self._axis.index] = factor
            return v
        return Vector((factor, factor, factor))

    def _update(self, context, event):
        opts = get_options(context)
        dy = self.start_y - event.mouse_region_y
        factor = max(0.01, 1.0 + dy * 0.01)
        factor_vec = self._factor_vector(factor)

        self.obj.matrix_world = self.init_matrix.copy()
        self.obj.scale = Vector(
            self.init_scale[i] * factor_vec[i] for i in range(3)
        )

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
            transform_mode=TransformMode.SCALE,
        )

        if result.snapped:
            self.obj.matrix_world = self.init_matrix.copy()
            self.obj.scale = self.init_scale.copy()
            apply_object_scale(self.obj, result.scale, self.pivot)

        push_guides(
            context,
            region=self.region,
            rv3d=self.rv3d,
            result=result,
            depth_co=self.obj.matrix_world.translation,
        )
        self._set_header(context, factor, result)

    def _set_header(self, context, factor, result):
        axis = self._axis.name if self._axis.active else ""
        set_header(context, header_text(self.bl_label, axis, f"{factor:.3f}×", result.snapped))

    def _finish(self, context):
        draw.disable()
        clear_header(context)
        context.area.tag_redraw()
        return {"FINISHED"}

    def _cancel(self, context):
        self.obj.matrix_world = self.init_matrix
        self.obj.scale = self.init_scale
        draw.disable()
        clear_header(context)
        context.area.tag_redraw()
        return {"CANCELLED"}


def register():
    bpy.utils.register_class(MAGNETS_OT_scale)


def unregister():
    bpy.utils.unregister_class(MAGNETS_OT_scale)
