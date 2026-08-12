"""Edit-mode mesh feature extraction via bmesh."""

from __future__ import annotations

from mathutils import Vector

from ..core.features import (
    EntityRef,
    FeaturePool,
    LineFeature,
    PlaneFeature,
    PointFeature,
    PointKind,
)


def edit_mesh_feature_pool(obj, bm) -> FeaturePool:
    """Extract features from selected bmesh elements.

    Args:
        obj: Blender mesh object in Edit Mode.
        bm: Active bmesh for ``obj``.

    Returns:
        FeaturePool of selected points, edges, and faces.
    """
    mw = obj.matrix_world
    ref = EntityRef(name=obj.name)
    pool = FeaturePool()

    sel_verts = [v for v in bm.verts if v.select]
    sel_edges = [e for e in bm.edges if e.select]
    sel_faces = [f for f in bm.faces if f.select]

    for v in sel_verts:
        pool.points.append(PointFeature(mw @ v.co, PointKind.VERTEX, ref))
        # Unselected linked edges → continuation direction features.
        for e in v.link_edges:
            if not e.select:
                other_v = e.other_vert(v)
                direction = (v.co - other_v.co)
                if direction.length_squared > 0:
                    dir_world = (mw.to_3x3() @ direction).normalized()
                    pool.lines.append(
                        LineFeature(mw @ v.co, dir_world, "edge continuation", ref)
                    )
                # Unselected linked faces → tangent-continuity planes.
                for f in e.link_faces:
                    if not f.select:
                        center = Vector((0.0, 0.0, 0.0))
                        for fv in f.verts:
                            center += fv.co
                        center /= len(f.verts)
                        center_world = mw @ center
                        normal_world = (mw.to_3x3() @ f.normal).normalized()
                        pool.planes.append(PlaneFeature(center_world, normal_world, "tangent continuity", ref))

    for e in sel_edges:
        a = mw @ e.verts[0].co
        b = mw @ e.verts[1].co
        direction = b - a
        if direction.length_squared == 0.0:
            continue
        mid = (a + b) * 0.5
        pool.points.append(PointFeature(mid, PointKind.MIDPOINT, ref))
        pool.lines.append(
            LineFeature(a.copy(), direction.normalized(), "edge", ref)
        )

    for f in sel_faces:
        center = Vector((0.0, 0.0, 0.0))
        for fv in f.verts:
            center += fv.co
        center /= len(f.verts)
        center_world = mw @ center
        normal = (mw.to_3x3() @ f.normal).normalized()
        pool.points.append(PointFeature(center_world, PointKind.FACE, ref))
        pool.planes.append(PlaneFeature(center_world, normal, "face", ref))

    if not pool.points and not pool.lines and not pool.planes:
        pool.points.append(PointFeature(mw.translation.copy(), PointKind.ORIGIN, ref))

    return pool


def apply_edit_translation(obj, bm, delta: Vector):
    """Translate selected mesh elements in world space.

    Args:
        obj: Blender mesh object in Edit Mode.
        bm: Active bmesh for ``obj``.
        delta: World-space translation.
    """
    inv = obj.matrix_world.inverted()
    local_delta = inv.to_3x3() @ delta
    for v in bm.verts:
        if v.select:
            v.co += local_delta
    bm.normal_update()


def snapshot_selected_verts(bm) -> dict[int, Vector]:
    """Snapshot selected vertex world coordinates."""
    return {v.index: v.co.copy() for v in bm.verts if v.select}


def restore_selected_verts(bm, snapshot: dict[int, Vector]):
    """Restore selected vertices from a world-space snapshot.

    Args:
        obj: Mesh object in Edit Mode.
        bm: Active bmesh.
        snapshot: Mapping produced by ``snapshot_selected_verts``.
    """
    for v in bm.verts:
        if v.index in snapshot:
            v.co = snapshot[v.index].copy()
    bm.normal_update()
