"""Fast solver paths give the same results as the plain nested scans.

The references below are the original brute-force loops. The solvers now
index candidates by coordinate, prefilter clearly-out-of-range pairs, build
midpoints once, and skip exact duplicates; none of that may change what they
return (or its order, which breaks ranking ties).
"""

import random

import core.solvers  # noqa: F401 - register solver table
from core.features import POINT_PRIORITY, EntityRef, PointFeature, PointKind
from core.frames import matrix_axes, world_axes
from core.geometry import reflect_point
from core.solvers.alignment import AlignmentSolver
from core.solvers.base import SolveContext
from core.solvers.midpoint import MidpointSolver
from core.solvers.symmetry import _SYMMETRY_PLANES, SymmetrySolver
from core.spatial import SortedProjection
from mathutils import Matrix, Vector

_KINDS = (PointKind.ORIGIN, PointKind.BBOX_CORNER, PointKind.BBOX_FACE_CENTER)


def _cloud(seed, n_entities=12, per_entity=9, grid=0.25):
    """Points snapped to a coarse grid, so many share coordinates exactly."""
    rng = random.Random(seed)
    pts = []
    for e in range(n_entities):
        ref = EntityRef(f"obj{e}")
        base = Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(-1, 1)))
        for _ in range(per_entity):
            off = Vector(tuple(round(rng.uniform(-1, 1) / grid) * grid for _ in range(3)))
            pts.append(PointFeature(base + off, rng.choice(_KINDS), ref))
    return pts


def _mover(seed):
    rng = random.Random(seed + 100)
    ref = EntityRef("mover")
    base = Vector((rng.uniform(-2, 2), rng.uniform(-2, 2), 0.0))
    corners = [Vector((x, y, z)) * 0.5 for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    pts = [PointFeature(base + c, PointKind.BBOX_CORNER, ref) for c in corners]
    pts.append(PointFeature(base.copy(), PointKind.ORIGIN, ref))
    return pts


def _ctxs():
    rotated = matrix_axes(Matrix.Rotation(0.3, 4, "Z") @ Matrix.Rotation(0.2, 4, "X"))
    return [
        SolveContext(axes=world_axes(), world_tol=0.7),
        SolveContext(axes=rotated, world_tol=0.7),
        SolveContext(axes=world_axes(), world_tol=0.7, view_normal=Vector((0, 0, -1))),
    ]


def _sig(rels):
    return [
        (
            id(r.moving), id(r.targets[0]), r.axis, r.residual,
            tuple(r.delta.translation), tuple(getattr(r.guide, "point", r.guide.a)),
        )
        for r in rels
    ]


# ── Reference implementations (the original nested loops) ───────────────────


def _alignment_reference(moving, candidates, ctx):
    """Original scan, then the view filter, then first-of-duplicates."""
    out = []
    for m in moving:
        seen = set()
        for c in candidates:
            if c.entity_ref.name == m.entity_ref.name:
                continue
            w = m.co - c.co
            for ai, (axis_name, direction) in enumerate(ctx.axes.items()):
                along = w.dot(direction)
                if abs(along) > ctx.world_tol:
                    continue
                if ctx.direction_hidden(direction.normalized()):
                    continue  # the view filter drops it later anyway
                perp = w - along * direction
                guide_dir = perp.normalized() if perp.length > 1e-6 else None
                hidden = ctx.direction_hidden(guide_dir) if guide_dir is not None else False
                dup = (axis_name, c.entity_ref.name, c.kind, along, hidden)
                if dup in seen:
                    continue
                seen.add(dup)
                out.append((m, c, axis_name, abs(along), -along * direction))
    return out


def _symmetry_reference(moving, candidates, ctx):
    out = []
    for m in moving:
        for c in candidates:
            if c.entity_ref.name == m.entity_ref.name:
                continue
            mid = (m.co + c.co) * 0.5
            for plane_name, axis_key in _SYMMETRY_PLANES:
                normal = ctx.axes[axis_key]
                if ctx.direction_hidden(normal):
                    continue
                residual = (reflect_point(m.co, mid, normal) - c.co).length
                if residual <= ctx.world_tol:
                    out.append((m, c, plane_name, residual))
    return out


def _midpoint_reference(moving, candidates, ctx):
    out = []
    for m in moving:
        by_entity = {}
        for c in candidates:
            if c.entity_ref.name != m.entity_ref.name:
                by_entity.setdefault(c.entity_ref.name, []).append(c)
        for pts in by_entity.values():
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    a, b = pts[i], pts[j]
                    if a.kind != b.kind:
                        continue
                    residual = (m.co - (a.co + b.co) * 0.5).length
                    if residual <= ctx.world_tol:
                        out.append((m, a, b, residual))
    return out


# ── Tests ────────────────────────────────────────────────────────────────────


def test_sorted_projection_is_a_superset_of_the_exact_test():
    rng = random.Random(7)
    pts = [Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), 0.0)) for _ in range(300)]
    d = Vector((0.6, 0.8, 0.0))
    index = SortedProjection(pts, d)
    for _ in range(50):
        q = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), 0.0))
        tol = rng.uniform(0.0, 5.0)
        exact = {i for i, p in enumerate(pts) if abs((q - p).dot(d)) <= tol}
        near = index.near(q.dot(d), tol)
        assert exact <= set(near)
        assert len(near) == len(set(near)), "no index twice"
    assert SortedProjection([], d).near(0.0, 1.0) == []


def test_alignment_matches_reference_scan():
    solver = AlignmentSolver()
    skipped = 0
    for seed in range(4):
        cands, moving = _cloud(seed), _mover(seed)
        for ctx in _ctxs():
            got = solver.solve(moving, cands, ctx)
            ref = _alignment_reference(moving, cands, ctx)
            assert [(id(r.moving), id(r.targets[0]), r.axis, r.residual) for r in got] == [
                (id(m), id(c), axis, res) for m, c, axis, res, _d in ref
            ]
            assert [tuple(r.delta.translation) for r in got] == [tuple(d) for *_x, d in ref]
            raw = sum(
                1
                for m in moving
                for c in cands
                if c.entity_ref.name != m.entity_ref.name
                for d in ctx.axes.values()
                if abs((m.co - c.co).dot(d)) <= ctx.world_tol
                and not ctx.direction_hidden(d.normalized())
            )
            skipped += raw - len(got)
    assert skipped > 0, "the clouds must contain duplicates to skip"


def test_alignment_skips_axes_along_the_view_depth():
    moving, cands = _mover(0), _cloud(0)
    top = SolveContext(axes=world_axes(), world_tol=0.7, view_normal=Vector((0, 0, -1)))
    axes = {r.axis for r in AlignmentSolver().solve(moving, cands, top)}
    assert axes == {"X", "Y"}


def test_symmetry_matches_reference_scan():
    solver = SymmetrySolver()
    for seed in range(4):
        cands, moving = _cloud(seed), _mover(seed)
        for ctx in _ctxs():
            got = solver.solve(moving, cands, ctx)
            ref = _symmetry_reference(moving, cands, ctx)
            assert [(id(r.moving), id(r.targets[0]), r.label, r.residual) for r in got] == [
                (id(m), id(c), f"⇔ {plane}", res) for m, c, plane, res in ref
            ]


def test_midpoint_matches_reference_scan():
    solver = MidpointSolver()
    for seed in range(4):
        cands, moving = _cloud(seed), _mover(seed)
        ctx = SolveContext(axes=world_axes(), world_tol=0.7)
        got = solver.solve(moving, cands, ctx)
        ref = _midpoint_reference(moving, cands, ctx)
        assert [(id(r.moving), id(r.targets[0]), id(r.targets[1]), r.residual) for r in got] == [
            (id(m), id(a), id(b), res) for m, a, b, res in ref
        ]


def test_point_priority_is_cached_per_kind():
    ref = EntityRef("a")
    for kind in PointKind:
        p = PointFeature(Vector(), kind, ref)
        assert p.priority == POINT_PRIORITY[kind]
    a = PointFeature(Vector((1, 2, 3)), PointKind.ORIGIN, ref)
    assert a == PointFeature(Vector((1, 2, 3)), PointKind.ORIGIN, ref), "equality unchanged"
