"""View culling / candidate LOD unit tests (bpy-free core)."""

import numpy as np
from core.features import EntityRef, FeaturePool, LineFeature, PointFeature, PointKind
from core.frames import world_axes
from core.solvers.base import SolveContext
from core.view_lod import FAR_POINT_KINDS, ViewLOD, far_moving, project_points
from mathutils import Vector

# Orthographic top view: world x, y in [-10, 10] map to pixels [0, 1000].
ORTHO = (
    ((0.1, 0.0, 0.0, 0.0), (0.0, 0.1, 0.0, 0.0), (0.0, 0.0, -0.01, 0.0), (0.0, 0.0, 0.0, 1.0)),
    1000,
    1000,
)
# Perspective camera at the origin looking down -Z (w = -z).
PERSP = (
    ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, -1.0, -0.2), (0.0, 0.0, -1.0, 0.0)),
    1000,
    1000,
)


def _box(name, x, y, half=0.25, z=0.0):
    """Feature pool of a small box: corners, face centres, centroid, origin, an edge."""
    ref = EntityRef(name=name)
    pool = FeaturePool()
    for dx in (-half, half):
        for dy in (-half, half):
            pool.points.append(PointFeature(Vector((x + dx, y + dy, z)), PointKind.BBOX_CORNER, ref))
    for dx, dy in ((-half, 0), (half, 0), (0, -half), (0, half)):
        pool.points.append(PointFeature(Vector((x + dx, y + dy, z)), PointKind.BBOX_FACE_CENTER, ref))
    pool.points.append(PointFeature(Vector((x, y, z)), PointKind.CENTROID, ref))
    pool.points.append(PointFeature(Vector((x, y, z)), PointKind.ORIGIN, ref))
    pool.lines.append(LineFeature(Vector((x - half, y - half, z)), Vector((1, 0, 0)), "bbox_edge", ref))
    return pool


def _scene(*boxes):
    pool = FeaturePool()
    for box in boxes:
        pool.extend(box)
    return pool


def _moving_at(x, y):
    return np.array([[x - 0.25, y - 0.25, 0.0], [x + 0.25, y + 0.25, 0.0]])


def _tiers(pool, projection=ORTHO, at=(0.0, 0.0), max_near=8, rows=2):
    return ViewLOD(pool).tiers(
        projection, _moving_at(*at), margin_px=10.0, max_near=max_near, row_neighbours=rows
    )


def test_project_points_matches_region_mapping():
    xy, front = project_points(np.array([[0.0, 0.0, 0.0], [10.0, -5.0, 0.0]]), ORTHO)
    assert front.all()
    assert np.allclose(xy, [[500.0, 500.0], [1000.0, 250.0]])
    _xy, front = project_points(np.array([[0.0, 0.0, -1.0], [0.0, 0.0, 1.0]]), PERSP)
    assert front.tolist() == [True, False]


def test_off_screen_objects_are_culled():
    tiers = _tiers(_scene(_box("On", 2, 0), _box("Off", 40, 0)))
    assert "On" in tiers.near
    assert "Off" not in tiers.near and "Off" not in tiers.far


def test_near_is_capped_to_closest_and_rest_is_far():
    pool = _scene(*(_box(f"B{i}", 1.0 + i, 3.0 + i) for i in range(5)))
    tiers = _tiers(pool, max_near=2, rows=0)
    assert tiers.near == {"B0", "B1"}
    assert tiers.far == {"B2", "B3", "B4"}


def test_row_and_column_neighbours_are_near_beyond_the_cap():
    pool = _scene(
        _box("Close", 1.0, 1.0),
        _box("RowRight", 6.0, 0.0),
        _box("RowRight2", 8.0, 0.0),
        _box("ColUp", 0.0, 7.0),
        _box("Diagonal", 6.0, 6.0),
    )
    tiers = _tiers(pool, max_near=1, rows=1)
    # Closest overall, plus the nearest one on each side of the row / column.
    assert tiers.near == {"Close", "RowRight", "ColUp"}
    assert tiers.far == {"RowRight2", "Diagonal"}


def test_object_straddling_the_viewer_stays_near():
    ref = EntityRef(name="Ground")
    ground = FeaturePool(
        points=[
            PointFeature(Vector((0.0, -1.0, -5.0)), PointKind.BBOX_CORNER, ref),
            PointFeature(Vector((0.0, -1.0, 5.0)), PointKind.BBOX_CORNER, ref),
        ]
    )
    pool = _scene(ground, *(_box(f"B{i}", 0.5 * i, 0.0, z=-10.0) for i in range(3)))
    tiers = ViewLOD(pool).tiers(
        PERSP, np.array([[0.0, 0.0, -10.0]]), margin_px=10.0, max_near=1, row_neighbours=0
    )
    assert "Ground" in tiers.near


def test_pools_split_features_by_tier():
    pool = _scene(_box("Near", 1, 1), _box("Far", 5, 5))
    lod = ViewLOD(pool)
    tiers = lod.tiers(ORTHO, _moving_at(0, 0), margin_px=10.0, max_near=1, row_neighbours=0)
    near, far = lod.pools(tiers, {"alignment", "spacing"})
    assert {p.entity for p in near.points} == {"Near"}
    assert len(near.points) == 10 and len(near.lines) == 1
    assert {p.entity for p in far.points} == {"Far"}
    assert all(p.kind in FAR_POINT_KINDS for p in far.points)
    assert not far.lines
    # The near pool is fresh each call: callers append surfaces to it.
    near.points.clear()
    again, _far = lod.pools(tiers, {"alignment"})
    assert len(again.points) == 10
    # No alignment enabled: far objects offer nothing.
    _near, none = lod.pools(tiers, {"spacing"})
    assert not none.points


def test_view_change_recomputes_rectangles():
    lod = ViewLOD(_scene(_box("A", 12, 0)))
    assert not lod.tiers(ORTHO, _moving_at(0, 0), margin_px=0.0, max_near=8).near
    wide = ((ORTHO[0][0][0] / 2, 0.0, 0.0, 0.0),) + ORTHO[0][1:]
    tiers = lod.tiers((wide, 1000, 1000), _moving_at(0, 0), margin_px=0.0, max_near=8)
    assert tiers.near == {"A"}


def test_far_moving_keeps_min_centre_max_points():
    box = _box("M", 0, 0)
    assert {p.kind for p in far_moving(box).points} == set(FAR_POINT_KINDS)
    ref = EntityRef(name="Edit")
    verts = FeaturePool(points=[PointFeature(Vector((0, 0, 0)), PointKind.VERTEX, ref)])
    assert len(far_moving(verts).points) == 1


def test_max_screen_px_tightens_rank_order_only():
    base = SolveContext(
        axes=world_axes(), world_tol=1.0, passive_px=72.0,
        screen_dist=lambda _co, corr: corr.length * 100.0,
    )
    moving = PointFeature(Vector((0, 0, 0)), PointKind.ORIGIN, EntityRef(name="M"))
    corr = Vector((0.3, 0.0, 0.0))  # 30 px
    wide = base.rank_order("alignment", moving, 0.3, moving.co, corr)
    assert wide is not None
    tight = SolveContext(**{**base.__dict__, "max_screen_px": 20.0})
    assert tight.screen_limit == 20.0
    assert tight.rank_order("alignment", moving, 0.3, moving.co, corr) is None
    near = Vector((0.1, 0.0, 0.0))  # 10 px: same score either way
    assert tight.rank_order("alignment", moving, 0.1, moving.co, near) == base.rank_order(
        "alignment", moving, 0.1, moving.co, near
    )
