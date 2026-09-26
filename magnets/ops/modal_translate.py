"""Translate modal operator with edit-mode and multi-constraint support."""

from __future__ import annotations

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

from ..adapters.bmesh_extract import EditSelection, apply_edit_translation
from ..adapters.extract import object_feature_pool
from ..adapters.snapshot import InteractionSnapshot
from ..core.features import FeaturePool
from ..core.tolerance import SnapHysteresis
from ..core.transform import TransformMode
from ..draw import handler as draw
from ..properties import extract_options, get_options
from .modal_common import AxisConstraint, clear_header, is_nav_event, set_header
from .pipeline import push_guides, run_inference, set_world_location


class MAGNETS_OT_translate(bpy.types.Operator):
    """Modal translate with Magnets guides."""
    bl_idname = "magnets.translate"
    bl_label = "Magnets Grab"
    bl_description = "Move with Magnets geometric guides"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Return True when the operator can run in ``context``."""
        if context.space_data is None or context.space_data.type != "VIEW_3D":
            return False
        if not get_options(context).enabled:
            return False
        if context.mode == "OBJECT":
            return context.active_object is not None
        if context.mode == "EDIT_MESH":
            return (
                context.active_object is not None
                and context.active_object.type == "MESH"
            )
        return False

    def invoke(self, context, event):
        """Start the modal snapping session."""
        self.obj = context.active_object
        self.region = context.region
        self.rv3d = context.region_data
        self.edit_mode = context.mode == "EDIT_MESH"
        self._snap = SnapHysteresis()
        self._axis = AxisConstraint()
        opts = get_options(context)

        if self.edit_mode:
            self.objs = [self.obj]
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            # Captured once: per-event work then touches only the selection.
            self._sel = EditSelection(self.obj, self.bm)
            self._vert_start = [v.co.copy() for v in self._sel.verts]
            self.init_world = self._sel.centroid_world()
        else:
            self.objs = list(context.selected_objects) or [self.obj]
            self.bm = None
            self._sel = None
            self._vert_start = []
            self._init_locs = {
                obj: obj.matrix_world.translation.copy() for obj in self.objs
            }
            self.init_world = self.obj.matrix_world.translation.copy()

        self.start_ref = view3d_utils.region_2d_to_location_3d(
            self.region,
            self.rv3d,
            (event.mouse_region_x, event.mouse_region_y),
            self.init_world,
        )

        exclude = list(self.objs) if not self.edit_mode else []
        self._snapshot = InteractionSnapshot.from_context(
            context,
            exclude=exclude,
            surfaces=opts.enable_tangency,
            **extract_options(opts),
        )

        draw.enable()
        context.window_manager.modal_handler_add(self)
        self._update(context, event)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def _restore_verts(self):
        for v, co in zip(self._sel.verts, self._vert_start, strict=True):
            v.co = co

    def modal(self, context, event):
        """Handle a modal event."""
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

    def _moving_pool(self, context) -> FeaturePool:
        opts = extract_options(get_options(context))
        if self.edit_mode:
            return self._sel.feature_pool()
        pool = FeaturePool()
        for obj in self.objs:
            pool.extend(object_feature_pool(obj, **opts))
        return pool

    def _apply_free(self, free_delta: Vector):
        if self.edit_mode:
            # Normals are refreshed once on finish, not on every mouse move.
            self._restore_verts()
            apply_edit_translation(
                self.obj, self.bm, free_delta,
                verts=self._sel.verts, update_normals=False,
            )
            bmesh.update_edit_mesh(self.obj.data)
        else:
            for obj in self.objs:
                set_world_location(obj, self._init_locs[obj] + free_delta)

    def _anchor(self) -> Vector:
        if self.edit_mode:
            return self._sel.centroid_world()
        center = Vector((0.0, 0.0, 0.0))
        for obj in self.objs:
            center += obj.matrix_world.translation
        return center / len(self.objs)

    def _update(self, context, event):
        cur = view3d_utils.region_2d_to_location_3d(
            self.region,
            self.rv3d,
            (event.mouse_region_x, event.mouse_region_y),
            self.init_world,
        )
        free_delta = self._axis.project(cur - self.start_ref)
        self._apply_free(free_delta)

        anchor = self._anchor()
        moving = self._moving_pool(context)

        result = run_inference(
            context,
            region=self.region,
            rv3d=self.rv3d,
            snapshot=self._snapshot,
            moving=moving,
            anchor_world=anchor,
            snap=self._snap,
            transform_mode=TransformMode.TRANSLATE,
        )

        if result.snapped:
            correction = self._axis.project(result.translation)
            if self.edit_mode:
                apply_edit_translation(
                    self.obj, self.bm, correction,
                    verts=self._sel.verts, update_normals=False,
                )
                bmesh.update_edit_mesh(self.obj.data)
            else:
                for obj in self.objs:
                    set_world_location(
                        obj, obj.matrix_world.translation + correction
                    )

        push_guides(
            context,
            region=self.region,
            rv3d=self.rv3d,
            result=result,
            depth_co=self._anchor(),
        )
        self._set_header(context, free_delta, result)

    def _set_header(self, context, free_delta, result):
        axis = f" [{self._axis.name}]" if self._axis.active else ""
        snap = "  ·  snapped" if result.snapped else ""
        set_header(
            context,
            f"Magnets Grab{axis}: "
            f"Dx {free_delta.x:.3f}  Dy {free_delta.y:.3f}  Dz {free_delta.z:.3f}"
            f"   (X/Y/Z lock axis){snap}",
        )

    def _finish(self, context):
        if self.edit_mode and self.bm is not None:
            self.bm.normal_update()
            bmesh.update_edit_mesh(self.obj.data)
        draw.disable()
        clear_header(context)
        context.area.tag_redraw()
        return {"FINISHED"}

    def _cancel(self, context):
        if self.edit_mode and self.bm is not None:
            self._restore_verts()
            self.bm.normal_update()
            bmesh.update_edit_mesh(self.obj.data)
        else:
            for obj in self.objs:
                set_world_location(obj, self._init_locs[obj])
        draw.disable()
        clear_header(context)
        context.area.tag_redraw()
        return {"CANCELLED"}


def register():
    """Register Blender classes / handlers for this module."""
    bpy.utils.register_class(MAGNETS_OT_translate)


def unregister():
    """Unregister Blender classes / handlers for this module."""
    bpy.utils.unregister_class(MAGNETS_OT_translate)
