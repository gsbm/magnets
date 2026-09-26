"""Edit-mode mesh feature extraction via bmesh."""

from __future__ import annotations

from mathutils import Vector

from ..core.bbox import bbox_face_centers
from ..core.features import (
    EntityRef,
    FeaturePool,
    LineFeature,
    PlaneFeature,
    PointFeature,
    PointKind,
)

# Above this many selected vertices the selection is summarised by its
# bounding box (corners, face centers, center) instead of one feature per
# element: per-element features cost ~5 us each per tick and swamp the solvers.
DETAIL_LIMIT = 2048

# Vertices sampled to track a summarised selection's centroid each tick.
_CENTROID_SAMPLES = 256


def _face_center(face) -> Vector:
    center = Vector((0.0, 0.0, 0.0))
    for fv in face.verts:
        center += fv.co
    return center / len(face.verts)


def _detailed_pool(obj, verts, edges, faces) -> FeaturePool:
    """One feature per selected element (small selections)."""
    mw = obj.matrix_world
    basis = mw.to_3x3()
    ref = EntityRef(name=obj.name)
    pool = FeaturePool()

    for v in verts:
        v_world = mw @ v.co
        pool.points.append(PointFeature(v_world, PointKind.VERTEX, ref))
        # Unselected linked edges → continuation direction features.
        for e in v.link_edges:
            if e.select:
                continue
            direction = v.co - e.other_vert(v).co
            if direction.length_squared > 0:
                pool.lines.append(
                    LineFeature(
                        v_world.copy(),
                        (basis @ direction).normalized(),
                        "edge continuation",
                        ref,
                    )
                )
            # Unselected linked faces → tangent-continuity planes.
            for f in e.link_faces:
                if not f.select:
                    pool.planes.append(
                        PlaneFeature(
                            mw @ _face_center(f),
                            (basis @ f.normal).normalized(),
                            "tangent continuity",
                            ref,
                        )
                    )

    for e in edges:
        a = mw @ e.verts[0].co
        b = mw @ e.verts[1].co
        direction = b - a
        if direction.length_squared == 0.0:
            continue
        pool.points.append(PointFeature((a + b) * 0.5, PointKind.MIDPOINT, ref))
        pool.lines.append(LineFeature(a.copy(), direction.normalized(), "edge", ref))

    for f in faces:
        center_world = mw @ _face_center(f)
        pool.points.append(PointFeature(center_world, PointKind.FACE, ref))
        pool.planes.append(
            PlaneFeature(center_world, (basis @ f.normal).normalized(), "face", ref)
        )
    return pool


def _bbox_pool(obj, lo: Vector, hi: Vector) -> FeaturePool:
    """World-axis bounding-box features of a large selection."""
    ref = EntityRef(name=obj.name)
    corners = [
        Vector((
            hi.x if i & 4 else lo.x,
            hi.y if i & 2 else lo.y,
            hi.z if i & 1 else lo.z,
        ))
        for i in range(8)
    ]
    pool = FeaturePool()
    for co in corners:
        pool.points.append(PointFeature(co, PointKind.BBOX_CORNER, ref))
    for co in bbox_face_centers(corners):
        pool.points.append(PointFeature(co, PointKind.BBOX_FACE_CENTER, ref))
    pool.points.append(PointFeature((lo + hi) * 0.5, PointKind.CENTROID, ref))
    return pool


class EditSelection:
    """The selected part of an edit mesh, captured once per drag.

    Scanning every vertex, edge and face of the mesh on each tick made Edit
    Mode drags on dense meshes crawl (~30 ms per tick with 64 of 250k vertices
    selected, ~700 ms with half the mesh). The one full scan now happens here;
    ticks touch only the selection (small ones) or a fixed sample (large ones).

    Element references stay valid while the transform runs because it moves
    vertices without changing topology. ``ReferenceError`` means the edit mesh
    was rebuilt; callers then capture a new selection.
    """

    def __init__(self, obj, bm):
        self.obj = obj
        self.bm = bm
        self.verts = [v for v in bm.verts if v.select]
        self.detailed = len(self.verts) <= DETAIL_LIMIT
        if self.detailed:
            self.edges = [e for e in bm.edges if e.select]
            self.faces = [f for f in bm.faces if f.select]
            return
        self.edges = []
        self.faces = []
        # Large selection: the six world-axis extreme vertices bound it (exact
        # while it translates), and a fixed sample tracks its centroid.
        mw = obj.matrix_world
        world = [mw @ v.co for v in self.verts]
        self._extremes = []
        for axis in range(3):
            lo = min(range(len(world)), key=lambda i: world[i][axis])
            hi = max(range(len(world)), key=lambda i: world[i][axis])
            self._extremes += [self.verts[lo], self.verts[hi]]
        step = max(1, len(self.verts) // _CENTROID_SAMPLES)
        self._sample = self.verts[::step]
        self._sample_start = [v.co.copy() for v in self._sample]
        total = Vector((0.0, 0.0, 0.0))
        for v in self.verts:
            total += v.co
        self._centroid_start = total / len(self.verts)

    def centroid_world(self) -> Vector:
        """World-space centroid of the selection (object origin if empty)."""
        mw = self.obj.matrix_world
        if not self.verts:
            return mw.translation.copy()
        if self.detailed:
            center = Vector((0.0, 0.0, 0.0))
            for v in self.verts:
                center += v.co
            return mw @ (center / len(self.verts))
        # Start centroid moved by the sample's mean displacement: exact for a
        # translate (every selected vertex moves alike), close for rotate/scale.
        shift = Vector((0.0, 0.0, 0.0))
        for v, start in zip(self._sample, self._sample_start, strict=True):
            shift += v.co - start
        return mw @ (self._centroid_start + shift / len(self._sample))

    def feature_pool(self) -> FeaturePool:
        """Moving features for the current vertex positions."""
        obj = self.obj
        if self.detailed:
            pool = _detailed_pool(obj, self.verts, self.edges, self.faces)
        else:
            mw = obj.matrix_world
            pts = [mw @ v.co for v in self._extremes]
            lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
            hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
            pool = _bbox_pool(obj, lo, hi)
        if not pool.points and not pool.lines and not pool.planes:
            ref = EntityRef(name=obj.name)
            pool.points.append(
                PointFeature(obj.matrix_world.translation.copy(), PointKind.ORIGIN, ref)
            )
        return pool


def apply_edit_translation(obj, bm, delta: Vector, verts=None, update_normals=True):
    """Translate selected mesh elements in world space.

    Args:
        obj: Blender mesh object in Edit Mode.
        bm: Active bmesh for ``obj``.
        delta: World-space translation.
        verts: The selected vertices, when already known (skips a full scan).
        update_normals: Recompute normals (a full-mesh pass). Interactive
            callers skip it per event and refresh once when done.
    """
    inv = obj.matrix_world.inverted()
    local_delta = inv.to_3x3() @ delta
    if verts is None:
        verts = [v for v in bm.verts if v.select]
    for v in verts:
        v.co += local_delta
    if update_normals:
        bm.normal_update()
