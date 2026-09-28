"""Fast solver paths give the same results as plain nested scans.

The references below are the original brute-force loops followed by the
best-per-key rule, written independently: of all pairs sharing a rank key,
keep the lowest order value (earliest on ties), emitted in first-visit order.
The solvers index candidates by coordinate, prefilter clearly-out-of-range
pairs and build midpoints once; none of that may change what they return
(or its order, which breaks ranking ties).
"""

import random

import core.solvers  # noqa: F401 - register solver table
from core.features import POINT_PRIORITY, EntityRef, PointFeature, PointKind
from core.frames import matrix_axes, world_axes
from core.geometry import reflect_point
from core.scoring import RankItem, best_per_key, score_parts
from core.solvers.alignment import AlignmentSolver
from core.solvers.base import BestPerKey, SolveContext
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


def _ctxs(tol=0.7):
    rotated = matrix_axes(Matrix.Rotation(0.3, 4, "Z") @ Matrix.Rotation(0.2, 4, "X"))
    return [
        SolveContext(axes=world_axes(), world_tol=tol),
        SolveContext(axes=rotated, world_tol=tol),
        SolveContext(axes=world_axes(), world_tol=tol, view_normal=Vector((0, 0, -1))),
    ]


def _reduce(entries):
    """Reference best-per-key: ``entries`` are (key, order, payload) in visit order."""
    best = {}
    for seq, (key, order, payload) in enumerate(entries):
        if key not in best or order < best[key][0]:
            best[key] = (order, seq, payload)
    return [payload for _o, _s, payload in sorted(best.values(), key=lambda t: t[1])]


# ── Reference implementations (the original nested loops) ───────────────────


def _alignment_reference(moving, candidates, ctx):
    entries = []
    for m in moving:
        for c in candidates:
            if c.entity_ref.name == m.entity_ref.name:
                continue
            w = m.co - c.co
            for axis_name, direction in ctx.axes.items():
                along = w.dot(direction)
                if abs(along) > ctx.world_tol:
                    continue
                if ctx.direction_hidden(direction.normalized()):
                    continue  # the view filter drops it later anyway
                perp = w - along * direction
                if perp.length > 1e-6 and ctx.direction_hidden(perp.normalized()):
                    continue  # guide seen end-on: filtered out
                key = (axis_name, c.entity_ref.name, m.kind, c.kind)
                entries.append((key, abs(along), (m, c, axis_name, abs(along), -along * direction)))
    return _reduce(entries)


def _symmetry_reference(moving, candidates, ctx):
    entries = []
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
                    key = (plane_name, c.entity_ref.name, m.kind, c.kind)
                    entries.append((key, (residual,), (m, c, plane_name, residual)))
    return _reduce(entries)


def _midpoint_reference(moving, candidates, ctx):
    entries = []
    for m in moving:
        by_entity = {}
        for c in candidates:
            if c.entity_ref.name != m.entity_ref.name:
                by_entity.setdefault(c.entity_ref.name, []).append(c)
        for name, pts in by_entity.items():
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    a, b = pts[i], pts[j]
                    if a.kind != b.kind or ctx.direction_hidden(b.co - a.co):
                        continue
                    residual = (m.co - (a.co + b.co) * 0.5).length
                    if residual <= ctx.world_tol:
                        entries.append(((name, m.kind, a.kind), (residual,), (m, a, b, residual)))
    return _reduce(entries)


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
    for seed in range(4):
        cands, moving = _cloud(seed), _mover(seed)
        for ctx in _ctxs():
            got = solver.solve(moving, cands, ctx)
            ref = _alignment_reference(moving, cands, ctx)
            assert [(id(r.moving), id(r.targets[0]), r.axis, r.residual) for r in got] == [
                (id(m), id(c), axis, res) for m, c, axis, res, _d in ref
            ]
            assert [tuple(r.delta.translation) for r in got] == [tuple(d) for *_x, d in ref]


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
    found = 0
    for seed in range(4):
        cands, moving = _cloud(seed), _mover(seed)
        for ctx in _ctxs(tol=1.5):
            got = solver.solve(moving, cands, ctx)
            ref = _midpoint_reference(moving, cands, ctx)
            assert [(id(r.moving), id(r.targets[0]), id(r.targets[1]), r.residual) for r in got] == [
                (id(m), id(a), id(b), res) for m, a, b, res in ref
            ]
            found += len(got)
    assert found > 0


def test_best_per_key_collector():
    best = BestPerKey()
    best.offer("a", 3.0, "a3")
    best.offer("b", 1.0, "b1")
    best.offer("a", 2.0, "a2")  # better: replaces, keeps its own visit order
    best.offer("a", 2.0, "a2-tie")  # tie: earliest stays
    best.offer("c", None, "dropped")  # would be dropped by ranking
    assert best.winners() == ["b1", "a2"]


def test_rank_order_uses_screen_distance_and_passive_range():
    m = PointFeature(Vector(), PointKind.BBOX_CORNER, EntityRef("m"))
    ctx = SolveContext(axes=world_axes(), world_tol=1.0, passive_px=50.0)
    assert ctx.rank_order("symmetry", m, 0.2, m.co, Vector((1, 0, 0))) == (0.2,)
    ctx.screen_dist = lambda _co, corr: corr.length * 100.0  # 1 m = 100 px
    near = ctx.rank_order("symmetry", m, 0.2, m.co, Vector((0.1, 0, 0)))
    far = ctx.rank_order("symmetry", m, 0.1, m.co, Vector((0.3, 0, 0)))
    assert near < far, "a nearer correction outranks a smaller residual"
    sd = Vector((0.1, 0, 0)).length * 100.0  # ~10 px (single-precision Vector)
    expected = score_parts("symmetry", POINT_PRIORITY[PointKind.BBOX_CORNER], 0.2, sd, 50.0, 1.0)
    assert near == (-expected, sd)
    assert ctx.rank_order("symmetry", m, 0.1, m.co, Vector((0.6, 0, 0))) is None, "beyond range"
    ctx.screen_dist = lambda _co, _corr: None
    assert ctx.rank_order("symmetry", m, 0.1, m.co, Vector((0.1, 0, 0))) is None, "off-screen"


def test_scoring_best_per_key_keeps_the_item_rank_would_pick():
    def item(key, score, dist, tag):
        return RankItem(key=key, score=score, screen_dist=dist, payload=tag)

    items = [item("a", 1.0, 5.0, "a-low"), item("b", 2.0, 1.0, "b"),
             item("a", 3.0, 9.0, "a-high"), item("a", 3.0, 4.0, "a-high-near"),
             item("a", 3.0, 4.0, "a-tie")]
    assert [it.payload for it in best_per_key(items)] == ["b", "a-high-near"]


def test_point_priority_is_cached_per_kind():
    ref = EntityRef("a")
    for kind in PointKind:
        assert PointFeature(Vector(), kind, ref).priority == POINT_PRIORITY[kind]
    a = PointFeature(Vector((1, 2, 3)), PointKind.ORIGIN, ref)
    assert a == PointFeature(Vector((1, 2, 3)), PointKind.ORIGIN, ref), "equality unchanged"
