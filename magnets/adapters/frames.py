"""Reference-frame axis extraction using bpy."""

from __future__ import annotations

from mathutils import Matrix

from ..core.frames import Frame, matrix_axes, view_axes, world_axes


def _collection_instance_matrix(context, collection):
    """Matrix of a collection-instance empty referencing ``collection``, if any."""
    for obj in context.view_layer.objects:
        if (
            getattr(obj, "instance_type", None) == "COLLECTION"
            and getattr(obj, "instance_collection", None) == collection
        ):
            return obj.matrix_world.copy()
    return None


def frame_axes(
    context,
    obj,
    frame: Frame,
    custom_matrix: Matrix | None = None,
    custom_object=None,
):
    """Resolve X/Y/Z axis directions for a reference frame.

    Args:
        context: Blender context.
        obj: Moving object (for local/parent frames).
        frame: Requested Frame.
        view_matrix: Optional view matrix for Frame.VIEW.
        custom_obj: Optional custom reference object.

    Returns:
        Mapping of axis name to unit world Vector.
    """
    if frame == Frame.WORLD:
        return world_axes()
    if frame == Frame.LOCAL:
        return matrix_axes(obj.matrix_world)
    if frame == Frame.VIEW:
        rv3d = context.region_data
        if rv3d is not None:
            return view_axes(rv3d.view_matrix)
        return world_axes()
    if frame == Frame.PARENT:
        if obj.parent is not None:
            return matrix_axes(obj.parent.matrix_world)
        return matrix_axes(obj.matrix_world)
    if frame == Frame.COLLECTION:
        if obj.users_collection:
            coll = obj.users_collection[0]
            inst = _collection_instance_matrix(context, coll)
            if inst is not None:
                return matrix_axes(inst)
        return world_axes()
    if frame == Frame.CUSTOM:
        if custom_object is not None:
            return matrix_axes(custom_object.matrix_world)
        if custom_matrix is not None:
            return matrix_axes(custom_matrix)
        return world_axes()
    return world_axes()
