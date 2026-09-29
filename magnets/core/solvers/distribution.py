"""Distribution solver: equal gaps between distinct objects.

Supports rhythm (extend an even row) and equalize (center between
neighbours), measured per ``SolveContext.spacing_metric``.
"""

from __future__ import annotations

from dataclasses import dataclass

from mathutils import Vector

from ..features import FeatureType, PointFeature
from ..relationship import ConstraintDelta, GuideSpans, Relationship
from .base import SolveContext, Solver


@dataclass
class _Neighbour:
    """A candidate object reduced to its position along one axis."""

    center_pt: PointFeature
    s: float  # centre coordinate along the axis
    lo: float  # nearest edge (min projection)
    hi: float  # far edge (max projection)


def _by_entity(points: list[PointFeature]) -> dict[str, list[PointFeature]]:
    groups: dict[str, list[PointFeature]] = {}
    for p in points:
        groups.setdefault(p.entity_ref.name, []).append(p)
    return groups


def _representative(points: list[PointFeature]) -> PointFeature:
    """Return an entity's highest-priority point (origin/centroid) as its centre."""
    return max(points, key=lambda p: p.priority)


class DistributionSolver(Solver):
    """Equal-gap distribution between objects."""
    family = "spacing"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        return (FeatureType.POINT, FeatureType.POINT)

    def solve(
        self,
        moving: list[PointFeature],
        candidates: list[PointFeature],
        ctx: SolveContext,
    ) -> list[Relationship]:
        tol = ctx.world_tol
        metric = getattr(ctx, "spacing_metric", "both")
        want_center = metric in ("center", "both")
        want_edge = metric in ("edge", "both")
        if not (want_center or want_edge):
            return []

        cand_by_ent = _by_entity(candidates)
        out: list[Relationship] = []

        for m_name, m_pts in _by_entity(moving).items():
            m_center_pt = _representative(m_pts)
            m_center = m_center_pt.co
            for axis_name, direction in ctx.axes.items():
                if direction.length_squared < 1e-12:
                    continue
                u = direction.normalized()

                neighbours: list[_Neighbour] = []
                for name, pts in cand_by_ent.items():
                    if name == m_name:
                        continue
                    c_co = _representative(pts).co
                    off = c_co - m_center
                    perp = (off - off.dot(u) * u).length
                    if perp > tol:  # not in the same row/column as the moving object
                        continue
                    projs = [p.co.dot(u) for p in pts]
                    neighbours.append(
                        _Neighbour(
                            center_pt=_representative(pts),
                            s=c_co.dot(u),
                            lo=min(projs),
                            hi=max(projs),
                        )
                    )
                if len(neighbours) < 2:
                    continue

                neighbours.sort(key=lambda n: n.s)
                m_s = m_center.dot(u)
                m_lo = min(p.co.dot(u) for p in m_pts)
                m_hi = max(p.co.dot(u) for p in m_pts)

                self._targets_for_axis(
                    out,
                    ctx=ctx,
                    axis_name=axis_name,
                    u=u,
                    m_center_pt=m_center_pt,
                    m_s=m_s,
                    m_lo=m_lo,
                    m_hi=m_hi,
                    neighbours=neighbours,
                    want_center=want_center,
                    want_edge=want_edge,
                )
        return out

    def _targets_for_axis(
        self,
        out: list[Relationship],
        *,
        ctx: SolveContext,
        axis_name: str,
        u: Vector,
        m_center_pt: PointFeature,
        m_s: float,
        m_lo: float,
        m_hi: float,
        neighbours: list[_Neighbour],
        want_center: bool,
        want_edge: bool,
    ) -> None:
        tol = ctx.world_tol
        # Offsets from the moving centre to its own near/far edges, so an
        # edge-anchored target can be converted back to a centre coordinate.
        pre = m_s - m_lo  # centre-to-near-edge
        post = m_hi - m_s  # centre-to-far-edge

        def world_at(s: float) -> Vector:
            # Map an axis coordinate onto the moving object's row line, so every
            # equal-spacing bar is drawn straight through the row.
            return m_center_pt.co + (s - m_s) * u

        def emit(
            target_s: float,
            gap: float,
            a: _Neighbour,
            b: _Neighbour,
            spans_s: tuple[tuple[float, float], ...],
        ) -> None:
            residual = abs(target_s - m_s)
            if residual > tol or gap <= tol:
                return
            gaps = tuple((world_at(s0), world_at(s1)) for s0, s1 in spans_s)
            out.append(
                Relationship(
                    family=self.family,
                    axis=axis_name,
                    label=ctx.format_length(gap),
                    moving=m_center_pt,
                    targets=(a.center_pt, b.center_pt),
                    residual=residual,
                    delta=ConstraintDelta.from_vector((target_s - m_s) * u),
                    guide=GuideSpans(gaps=gaps, axis=u.copy()),
                )
            )

        for i in range(len(neighbours) - 1):
            a, b = neighbours[i], neighbours[i + 1]

            # --- rhythm: continue an existing gap on either side of the pair ---
            if want_center:
                g = b.s - a.s
                # left of a: new gap [t, a] equals reference gap [a, b]
                emit(a.s - g, g, a, b, ((a.s - g, a.s), (a.s, b.s)))
                # right of b: new gap [b, t] equals [a, b]
                emit(b.s + g, g, a, b, ((b.s, b.s + g), (a.s, b.s)))
            if want_edge:
                g = b.lo - a.hi  # visible gap between the two neighbours' edges
                emit(a.lo - g - post, g, a, b, ((a.lo - g, a.lo), (a.hi, b.lo)))
                emit(b.hi + g + pre, g, a, b, ((b.hi, b.hi + g), (a.hi, b.lo)))

            # --- equalize: m sits between a and b, split the gap evenly ---
            if a.s < m_s < b.s:
                if want_center:
                    mid = 0.5 * (a.s + b.s)
                    half = mid - a.s
                    emit(mid, half, a, b, ((a.s, mid), (mid, b.s)))
                if want_edge:
                    span = b.lo - a.hi
                    half = (span - (m_hi - m_lo)) * 0.5
                    if half > tol:
                        left_hi = a.hi + half  # moving object's near edge
                        right_lo = left_hi + (m_hi - m_lo)  # its far edge
                        emit(
                            a.hi + half + pre,
                            half,
                            a,
                            b,
                            ((a.hi, left_hi), (right_lo, b.lo)),
                        )
