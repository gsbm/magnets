"""Coverage enhancement tests targeting untested branches in the core module."""

import math

from core.bbox import (
    bbox_bounding_sphere,
    bbox_centroid,
    bbox_dimensions,
    bbox_edges,
    bbox_face_centers,
    bbox_face_planes,
)
from core.features import (
    BBoxFeature,
    CircleFeature,
    DirectionFeature,
    EntityRef,
    LineFeature,
    PlaneFeature,
    PointFeature,
    PointKind,
    SurfaceFeature,
)
from core.labels import alignment_label, feature_hint
from core.relationship import (
    ConstraintDelta,
    GuideCircle,
    GuidePlane,
    GuideSegment,
    GuideSpans,
    Relationship,
)
from core.resolver import (
    clamp_translation_step,
    resolve_rotation,
    resolve_scale,
)
from core.scoring import RankItem
from core.tolerance import SnapHysteresis
from core.view_filter import guide_direction_visible, relationship_visible_in_view
from mathutils import Vector


# Test BBox with < 8 corners
def test_bbox_early_exits():
    assert bbox_face_centers([]) == []
    assert bbox_centroid([]) is None
    assert bbox_edges([]) == []
    assert bbox_face_planes([]) == []
    assert bbox_dimensions([]) is None
    assert bbox_bounding_sphere([]) is None

def test_bbox_functions():
    corners = [
        Vector((-1, -1, -1)), Vector((-1, -1, 1)), Vector((-1, 1, -1)), Vector((-1, 1, 1)),
        Vector((1, -1, -1)), Vector((1, -1, 1)), Vector((1, 1, -1)), Vector((1, 1, 1))
    ]
    assert len(bbox_face_centers(corners)) == 6
    assert bbox_centroid(corners) == Vector((0, 0, 0))
    center, radius = bbox_bounding_sphere(corners)
    assert center == Vector((0, 0, 0))
    assert abs(radius - math.sqrt(3)) < 1e-5

# Test labels
def test_labels():
    pt = PointFeature.from_name(Vector((0, 0, 0)), PointKind.ORIGIN, "obj")
    assert feature_hint(pt) == "origin"
    line = LineFeature(Vector(), Vector(), "my_edge", EntityRef("a"))
    assert feature_hint(line) == "my edge"
    plane = PlaneFeature(Vector(), Vector(), "my_plane", EntityRef("a"))
    assert feature_hint(plane) == "my plane"
    dir_feat = DirectionFeature(Vector(), Vector(), "my_dir", EntityRef("a"))
    assert feature_hint(dir_feat) == "my dir"
    bbox = BBoxFeature(Vector(), Vector(), EntityRef("a"))
    assert feature_hint(bbox) == "bbox"
    circle = CircleFeature(Vector(), Vector(), 1.0, "hole", EntityRef("a"))
    assert feature_hint(circle) == "hole"
    surface = SurfaceFeature(Vector(), Vector(), EntityRef("a"))
    assert feature_hint(surface) == "surface"

    class UnknownFeature:
        pass
    assert feature_hint(UnknownFeature()) == ""

    assert alignment_label("X", PointKind.ORIGIN, 0.0, 1.0) == "X"
    assert alignment_label("X", PointKind.ORIGIN, 0.5, 200.0) == "X · 100.0"
    assert alignment_label("X", PointKind.ORIGIN, 0.5, 20.0) == "X · 10.00"

# Test view filter
def test_guide_direction_visible():
    # Length zero test
    assert guide_direction_visible(Vector((0,0,0)), Vector((1,0,0))) is True
    assert guide_direction_visible(Vector((1,0,0)), Vector((0,0,0))) is True

    pt = PointFeature.from_name(Vector((0, 0, 0)), PointKind.ORIGIN, "obj")
    rel = Relationship(
        family="test", axis="X", label="", moving=pt, targets=(),
        residual=0.0, delta=ConstraintDelta.from_vector(Vector()),
        guide=GuideSegment(a=Vector((0,0,0)), b=Vector((1,0,0)))
    )
    # view normal None
    assert relationship_visible_in_view(rel, None) is True
    
    rel.guide = GuideSpans(gaps=((Vector((0,0,0)), Vector((1,0,0))),), axis=Vector((1,0,0)))
    assert relationship_visible_in_view(rel, Vector((0,0,1))) is True
    assert relationship_visible_in_view(rel, Vector((1,0,0))) is False
    
    rel.guide = GuideCircle(center=Vector((0,0,0)), normal=Vector((1,0,0)), radius=1.0)
    assert relationship_visible_in_view(rel, Vector((0,0,1))) is True
    assert relationship_visible_in_view(rel, Vector((1,0,0))) is False

    rel.guide = GuidePlane(point=Vector((0,0,0)), normal=Vector((1,0,0)))
    # For plane, edge-on if normal lies in view plane (dot = 0)
    assert relationship_visible_in_view(rel, Vector((0,0,1))) is False
    assert relationship_visible_in_view(rel, Vector((1,0,0))) is True
    
    # Unknown guide type
    rel.guide = object()
    assert relationship_visible_in_view(rel, Vector((1,0,0))) is True

# Test tolerance
def test_snap_hysteresis_methods():
    snap = SnapHysteresis()
    snap.remember_active_keys({("a", "b")})
    assert snap.sticky_keys == {("a", "b")}
    
    # Force break
    snap.active_key = ("a", "b")
    snap.force_break()
    assert snap.broken is True
    assert snap.active_key is None
    
    # Re-engage check
    item = RankItem(key=("x",), score=1, screen_dist=10.0, payload=1)
    snap.broken = True
    snap.pick_active([item], snap_px=5.0, hysteresis_px=1.0, reengage_margin_px=2.0) # > 7.0 clears break
    assert snap.broken is False
    
    # When latched item screen dist > release_px
    snap.active_key = ("x",)
    item_latched = RankItem(key=("x",), score=1, screen_dist=10.0, payload=1)
    snap._latched = item_latched
    snap.pick_active([item_latched], snap_px=5.0, hysteresis_px=1.0) # > 6.0
    assert snap.broken is True

# Test resolver
def test_resolver_scale_rotation():
    pt = PointFeature.from_name(Vector((0, 0, 0)), PointKind.ORIGIN, "obj")
    rel = Relationship("test", "X", "", pt, (), 0.0, ConstraintDelta(scale_factor=1.0, scale_axis=Vector((2,3,4))), None)
    # factor = 1.0, but scale_axis has length > 0
    assert resolve_scale([rel]) == Vector((2,3,4))
    
    # Empty active
    assert resolve_rotation([]) == (Vector((0,0,1)), 0.0)
    assert clamp_translation_step(Vector((1,0,0)), -1.0) == Vector((1,0,0))
    
    rel_rot = Relationship("test", "X", "", pt, (), 0.0, ConstraintDelta.from_rotation(Vector((1,0,0)), 0.0), None)
    # rotation_angle == 0.0
    assert resolve_rotation([rel_rot]) == (Vector((0,0,1)), 0.0)

from core.spatial import BVHIndex, HashGridIndex


def test_spatial_coverage():
    items = [(Vector((1,0,0)), "a")]
    idx = HashGridIndex(items, cell_size=1.0)
    assert idx.query_nearest(Vector((0,0,0)), 1) == ["a"]
    assert idx.query_nearest(Vector((0,0,0)), 0) == []
    assert len(idx) == 1
    
    bvh = BVHIndex(items)
    assert len(bvh) == 1
    assert bvh.query_radius(Vector((0,0,0)), 2.0) == ["a"]
    assert bvh.query_nearest(Vector((0,0,0)), 1) == ["a"]

# Test Solvers skipped branches
from core.frames import world_axes
from core.solvers.base import SolveContext
from core.solvers.tangency import SurfaceTangencySolver, TangencySolver


def _ctx(tol=1.0):
    return SolveContext(axes=world_axes(), world_tol=tol, unit_scale=1.0, surface_query_limit=1)

def test_tangency_coverage():
    m = CircleFeature(Vector((0,0,0)), Vector((0,0,1)), 1.0, "c", EntityRef("m"))
    # Perpendicular normal
    c1 = CircleFeature(Vector((0,0,0)), Vector((1,0,0)), 1.0, "c", EntityRef("t1"))
    # Dist <= tol
    c2 = CircleFeature(Vector((0.1,0,0)), Vector((0,0,1)), 1.0, "c", EntityRef("t2"))
    # Residual > tol
    c3 = CircleFeature(Vector((5,0,0)), Vector((0,0,1)), 1.0, "c", EntityRef("t3"))
    
    rels = TangencySolver().solve([m], [c1, c2, c3], _ctx(1.0))
    # Check that c2 produced a relationship (dist <= tol branch)
    assert any(r.targets[0].entity_ref.name == "t2" for r in rels)

    sm = PointFeature.from_name(Vector((0,0,0)), PointKind.ORIGIN, "m")
    s1 = SurfaceFeature(Vector((0,0,0)), Vector((0,0,1)), EntityRef("t1"))
    s2 = SurfaceFeature(Vector((10,0,0)), Vector((0,0,1)), EntityRef("t2"))
    rels2 = SurfaceTangencySolver().solve([sm], [s1, s2], _ctx(1.0))
    # Query limit is 1, so s2 shouldn't be processed
    assert len(rels2) == 1

from core.solvers.equal_size import EqualSizeSolver
from core.transform import TransformMode


def test_equal_size_coverage():
    m = BBoxFeature(Vector(), Vector((0,0,0)), EntityRef("m")) # dimension 0
    c = BBoxFeature(Vector(), Vector((1,1,1)), EntityRef("c"))
    solver = EqualSizeSolver()
    assert len(solver.solve([m], [c], _ctx())) == 0
    
    m2 = BBoxFeature(Vector(), Vector((1,1,1)), EntityRef("m"))
    c2 = BBoxFeature(Vector(), Vector((1.5,1.5,1.5)), EntityRef("c"))
    ctx = _ctx()
    ctx.transform_mode = TransformMode.SCALE
    rels = solver.solve([m2], [c2], ctx)
    assert len(rels) > 0
    assert rels[0].delta.scale_factor == 1.5

from core.solvers.spacing import SpacingSolver


def test_spacing_coverage():
    m = PointFeature.from_name(Vector((2,0,0)), PointKind.ORIGIN, "m")
    c1 = PointFeature.from_name(Vector((0,0,0)), PointKind.ORIGIN, "c")
    
    solver = SpacingSolver()
    # length < 2
    assert len(solver.solve([m], [c1], _ctx())) == 0
    
    # zero length line
    c3 = PointFeature.from_name(Vector((0,0,0)), PointKind.ORIGIN, "c")
    assert len(solver.solve([m], [c1, c3], _ctx())) == 0
    
    # not collinear
    c4 = PointFeature.from_name(Vector((0,1,0)), PointKind.ORIGIN, "c")
    assert len(solver.solve([m], [c1, c4], _ctx())) == 0

from core.solvers.symmetry import SymmetrySolver


def test_symmetry_coverage():
    m = PointFeature.from_name(Vector((1,0,0)), PointKind.ORIGIN, "m")
    c = PointFeature.from_name(Vector((10,10,10)), PointKind.ORIGIN, "c")
    assert len(SymmetrySolver().solve([m], [c], _ctx(0.1))) == 0 # residual > tol

from core.solvers.concentric import ConcentricSolver


def test_concentric_coverage():
    m = CircleFeature(Vector((0,0,0)), Vector((0,0,1)), 1.0, "c", EntityRef("m"))
    c1 = CircleFeature(Vector((0,0,0)), Vector((1,0,0)), 1.0, "c", EntityRef("c"))
    c2 = CircleFeature(Vector((10,0,0)), Vector((0,0,1)), 1.0, "c", EntityRef("c"))
    assert len(ConcentricSolver().solve([m], [c1], _ctx())) == 0 # normal dot < 0.9
    assert len(ConcentricSolver().solve([m], [c2], _ctx(0.1))) == 0 # residual > tol

from core.solvers.collinear import CollinearSolver
from core.solvers.coplanar import CoplanarSolver


def test_coplanar_collinear_coverage():
    m = PointFeature.from_name(Vector((10,0,0)), PointKind.ORIGIN, "m")
    cp = PlaneFeature(Vector((0,0,0)), Vector((1,0,0)), "plane", EntityRef("c"))
    assert len(CoplanarSolver().solve([m], [cp], _ctx(0.1))) == 0
    cl = LineFeature(Vector((0,0,0)), Vector((0,1,0)), "line", EntityRef("c"))
    assert len(CollinearSolver().solve([m], [cl], _ctx(0.1))) == 0
