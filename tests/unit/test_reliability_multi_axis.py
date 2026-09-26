"""Regression: all three alignment axes engage for two nearby objects.

X/Y/Z guides of nearby objects cluster on screen, and must not suppress each
other. Drives the real solver, scoring and resolver (screen projection
stubbed) and checks the axes compose into one translation.
"""

from __future__ import annotations

from core.features import PointFeature, PointKind
from core.frames import world_axes
from core.graph import build_active_set
from core.resolver import resolve_translation
from core.scoring import RankItem, rank, relationship_score
from core.solvers.alignment import AlignmentSolver
from core.solvers.base import SolveContext
from mathutils import Vector


def _cube_corners(center: Vector, half: float) -> list[Vector]:
    return [
        center + Vector((sx * half, sy * half, sz * half))
        for sx in (-1.0, 1.0)
        for sy in (-1.0, 1.0)
        for sz in (-1.0, 1.0)
    ]


def _rank_key(rel):
    def kind_of(feature):
        kind = getattr(feature, "kind", None)
        return getattr(kind, "value", kind)

    return (rel.family, rel.axis, rel.target_entity, kind_of(rel.moving), kind_of(rel.target))


def test_two_nearby_cubes_engage_all_three_axes_at_once():
    solver = AlignmentSolver()
    ctx = SolveContext(axes=world_axes(), world_tol=0.15, passive_px=48.0, snap_px=12.0, unit_scale=1.0)

    moving = [
        PointFeature.from_name(co, PointKind.BBOX_CORNER, "move")
        for co in _cube_corners(Vector((0.0, 0.0, 0.0)), 1.0)
    ]
    targets = [
        PointFeature.from_name(co, PointKind.BBOX_CORNER, "tgt")
        for co in _cube_corners(Vector((2.02, 2.02, 2.02)), 1.0)
    ]

    rels = solver.solve(moving, targets, ctx)
    by_axis = {}
    for rel in rels:
        by_axis.setdefault(rel.axis, rel)
    assert {"X", "Y", "Z"} <= set(by_axis)

    # Simulate screen metrics: all three anchors cluster within a couple of
    # pixels of each other, as they do in practice for two nearby objects.
    clustered_anchors = {"X": (100.0, 100.0), "Y": (102.0, 101.0), "Z": (104.0, 99.0)}
    items = []
    for axis in ("X", "Y", "Z"):
        rel = by_axis[axis]
        screen_dist = rel.residual * 100.0
        items.append(
            RankItem(
                key=_rank_key(rel),
                score=relationship_score(rel, screen_dist, ctx.passive_px, ctx.world_tol),
                screen_dist=screen_dist,
                payload=rel,
                screen_anchor=clustered_anchors[axis],
            )
        )

    ranked, visible = rank(items, passive_px=48.0, top_k=3, nms_px=20.0)
    assert {it.key[1] for it in ranked} == {"X", "Y", "Z"}

    primary = ranked[0]
    active = build_active_set(
        primary, ranked, snap_px=12.0, release_px=16.0, max_constraints=3, visible=visible
    )
    assert {rel.axis for rel in active} == {"X", "Y", "Z"}

    translation = resolve_translation(active)
    assert translation.length > 0.0
