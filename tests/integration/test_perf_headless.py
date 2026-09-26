"""Speed tests for drag start (scene cache) and Edit Mode ticks (headless).

Each check pairs a generous wall-clock budget with a deterministic work count
(cache hits, BVH builds, feature counts), so a regression is caught even on a
slow CI runner while noisy timings cannot cause flakes. Reference numbers
(Apple M-series, Blender 5.2) are in the comments; budgets leave >=5x slack.

Point the runner at Blender via ``BLENDER_BIN`` or have ``blender`` on PATH.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

INNER = rf"""
import sys
import time

sys.path.insert(0, r"{REPO_ROOT!s}")

import bmesh
import bpy
from mathutils import Matrix, Vector

import magnets

magnets.register()

from magnets import transform_overlay as ov
from magnets.adapters import scene_cache
from magnets.adapters.bmesh_extract import EditSelection
from magnets.adapters.snapshot import InteractionSnapshot
from magnets.properties import extract_options, get_options


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def timed(fn, repeat=1):
    t0 = time.perf_counter()
    for _ in range(repeat):
        out = fn()
    return (time.perf_counter() - t0) / repeat * 1000.0, out


ctx = bpy.context
opts = get_options(ctx)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# ── Drag start on a 400-object scene ─────────────────────────────────────────
N_LIGHT, N_HEAVY = 390, 10
for i in range(N_LIGHT):
    bpy.ops.mesh.primitive_cube_add(location=((i % 20) * 3.0, (i // 20) * 3.0, 0.0))
for i in range(N_HEAVY):  # ~50k tris each
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=160, ring_count=160, radius=1.0, location=(i * 3.0, -10.0, 0.0)
    )
bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 5.0))
mover = ctx.active_object
n_candidates = N_LIGHT + N_HEAVY

scene_cache.clear()
scene_cache.stats.reset()


def snapshot(surfaces):
    return InteractionSnapshot.from_context(
        ctx, exclude=[mover], surfaces=surfaces, **extract_options(opts)
    )


# Before: ~140 ms per drag (every object re-extracted, a BVH per mesh).
cold_ms, snap = timed(lambda: snapshot(True))
check(scene_cache.stats.bvh_builds == 0, "drag start must not build any BVH")
check(scene_cache.stats.feature_misses == n_candidates, "cold start extracts each object once")
check(len(snap.surface_index) == n_candidates, "every mesh is a surface candidate")

scene_cache.stats.reset()
warm_ms, _ = timed(lambda: snapshot(True))
check(scene_cache.stats.feature_hits == n_candidates, "warm start reuses every object")
check(scene_cache.stats.feature_misses == 0, "warm start re-extracts nothing")
check(scene_cache.stats.bvh_builds == 0, "warm start builds no BVH")
print(f"PERF drag start: cold={{cold_ms:.1f}} ms warm={{warm_ms:.1f}} ms (was ~140 ms)")
# Reference: cold ~22 ms, warm ~7 ms.
check(cold_ms < 120.0, f"cold drag start too slow: {{cold_ms:.1f}} ms")
check(warm_ms < 50.0, f"warm drag start too slow: {{warm_ms:.1f}} ms")

no_surf = snapshot(False)
check(no_surf.surface_index is None, "tangency off: no surface index at all")

# Only a moved object is re-extracted, and at its new position.
target = bpy.data.objects["Cube.001"]
target.location.z += 7.0
ctx.view_layer.update()
scene_cache.stats.reset()
snap = snapshot(True)
check(scene_cache.stats.feature_misses == 1, "only the moved object is re-extracted")
check(
    any(p.entity_ref.name == target.name and p.co.z > 6.0 for p in snap.pool.points),
    "moved object's features are at its new position",
)

# Surfaces: BVHs are lazy, local-space, and cached.
sphere = bpy.data.objects["Sphere"]  # at (0, -10, 0), radius 1
query = sphere.matrix_world.translation + Vector((0.0, 0.0, 1.5))
hits = snap.surface_index.query_nearest(query, 1.0, limit=4)
check(scene_cache.stats.bvh_builds == 1, "a query builds only the BVH it reaches")
check(
    hits and abs(hits[0].point.z - 1.0) < 0.02 and hits[0].normal.z > 0.9,
    "surface hit on a translated object (world vs local space)",
)
snap.surface_index.query_nearest(query, 1.0, limit=4)
check(scene_cache.stats.bvh_builds == 1, "BVH is reused by later queries")

# A rotated + non-uniformly scaled object: hits come back in world space.
sphere.matrix_world = (
    Matrix.Translation((0.0, -10.0, 0.0))
    @ Matrix.Rotation(0.7, 4, "X")
    @ Matrix.Diagonal((1.0, 1.0, 2.0, 1.0))
)
ctx.view_layer.update()
snap = snapshot(True)
# Query on the -X side: the next sphere sits at x=+3 and must stay out of reach.
side = Vector((-1.3, -10.0, 0.0))
hits = snap.surface_index.query_nearest(side, 1.0)
check(hits and abs(hits[0].point.x + 1.0) < 0.05, "transformed surface hit is in world space")
check(scene_cache.stats.bvh_builds == 1, "moving an object keeps its local-space BVH")

# Geometry edits invalidate the BVH (depsgraph handler).
sphere.data.transform(Matrix.Scale(0.5, 4))
sphere.data.update()
ctx.view_layer.update()
snapshot(True).surface_index.query_nearest(side, 1.0)
check(scene_cache.stats.bvh_builds == 2, "a geometry edit rebuilds that BVH")

# ── Edit Mode ticks on a dense mesh ──────────────────────────────────────────
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.mesh.primitive_grid_add(
    x_subdivisions=500, y_subdivisions=500, size=10.0, location=(0.0, 0.0, 20.0)
)
grid = ctx.active_object
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(grid.data)
check(len(bm.verts) > 250_000, "dense grid")


def select_first(n):
    for seq in (bm.verts, bm.edges, bm.faces):
        for elem in seq:
            elem.select = False
    for v in list(bm.verts)[:n]:
        v.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(grid.data)


class _FakeSession:
    edit_selection = None


def tick():
    # The per-tick work the overlay does in Edit Mode.
    ov._cheap_anchor(ctx)
    return ov._moving_target(ctx)


for label, n, budget_ms, max_points in (
    ("small", 64, 5.0, 400),      # before: ~30 ms/tick
    ("large", 125_000, 5.0, 16),  # before: ~700 ms/tick
):
    select_first(n)
    capture_ms, sel = timed(lambda: EditSelection(grid, bmesh.from_edit_mesh(grid.data)))
    session = _FakeSession()
    session.edit_selection = sel
    ov._session = session
    tick_ms, (_obj, pool, anchor, _edit, _bm) = timed(tick, repeat=10)
    print(
        f"PERF edit {{label}} ({{n}} verts selected): capture={{capture_ms:.1f}} ms "
        f"tick={{tick_ms:.2f}} ms moving_pts={{len(pool.points)}}"
    )
    # Reference: small tick ~0.26 ms, large tick ~0.05 ms.
    check(tick_ms < budget_ms, f"{{label}} edit tick too slow: {{tick_ms:.2f}} ms")
    check(len(pool.points) <= max_points, f"{{label}}: moving features bounded")
    check(sel.detailed == (n <= 2048), f"{{label}}: summarised only when large")

    # The tracked centroid stays exact under a translate of the selection.
    before = sel.centroid_world()
    for v in sel.verts:
        v.co.x += 0.25
    after = sel.centroid_world()
    check(
        abs((after - before).x - 0.25) < 1e-4 and abs((after - before).y) < 1e-6,
        f"{{label}}: centroid follows a translate exactly",
    )
    for v in sel.verts:
        v.co.x -= 0.25

ov._session = None
bpy.ops.object.mode_set(mode="OBJECT")
magnets.unregister()
print("MAGNETS_PERF_OK")
"""


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.mark.integration
def test_perf_headless(tmp_path):
    blender = _blender_bin()
    if not blender:
        pytest.skip("no Blender binary (set BLENDER_BIN or add blender to PATH)")

    script = tmp_path / "inner.py"
    script.write_text(INNER, encoding="utf-8")

    proc = subprocess.run(
        [blender, "--background", "--factory-startup", "--python", str(script)],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    sys.stdout.write("\n".join(ln for ln in proc.stdout.splitlines() if "PERF" in ln) + "\n")
    sys.stderr.write(proc.stderr[-3000:])
    assert "MAGNETS_PERF_OK" in proc.stdout, proc.stdout[-3000:]
