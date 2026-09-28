"""Symmetry solver."""

from __future__ import annotations

from ..features import FeatureType, PointFeature
from ..geometry import normalize, reflect_point
from ..relationship import ConstraintDelta, GuidePlane, Relationship
from .base import BestPerKey, SolveContext, Solver

_SYMMETRY_PLANES = (
    ("XY", "Z"),
    ("XZ", "Y"),
    ("YZ", "X"),
)


class SymmetrySolver(Solver):
    """Reflection symmetry solver."""
    family = "symmetry"

    def feature_types(self) -> tuple[FeatureType, FeatureType]:
        """Return the (moving, candidate) feature types this solver handles."""
        return (FeatureType.POINT, FeatureType.POINT)

    def solve(self, moving: list[PointFeature], candidates: list[PointFeature], ctx: SolveContext):
        """Return relationships between ``moving`` and ``candidates`` features."""
        out: list[Relationship] = []
        tol = ctx.world_tol
        # A plane facing an orthographic view is hidden by the view filter.
        planes = [
            (plane_name, ctx.axes[axis_key], normalize(ctx.axes[axis_key]))
            for plane_name, axis_key in _SYMMETRY_PLANES
            if not ctx.direction_hidden(ctx.axes[axis_key])
        ]
        # The residual is the part of (m - c) off the plane normal. This
        # prefilter only skips pairs clearly beyond ``tol`` (margin for
        # single-precision rounding); the exact test below is unchanged.
        reject2 = (tol * (1.0 + 1e-3) + 1e-6) ** 2
        best = BestPerKey() if ctx.best_per_key else None
        for m in moving:
            for c in candidates:
                if c.entity_ref.name == m.entity_ref.name:
                    continue
                w = m.co - c.co
                ww = w.dot(w)
                mid = None
                for plane_name, normal, unit in planes:
                    along = w.dot(unit)
                    if ww - along * along > reject2:
                        continue
                    if mid is None:
                        mid = (m.co + c.co) * 0.5
                    reflected = reflect_point(m.co, mid, normal)
                    residual = (reflected - c.co).length
                    if residual > tol:
                        continue
                    data = (m, c, plane_name, normal, residual, mid)
                    if best is not None:
                        # The correction is the full mirror move, not the
                        # residual: rank candidates as ranking will.
                        key = (plane_name, c.entity_ref.name, id(m.kind), id(c.kind))
                        order = ctx.rank_order(self.family, m, residual, m.co, c.co - m.co)
                        best.offer(key, order, data)
                        continue
                    out.append(self._relationship(*data))
        if best is not None:
            out = [self._relationship(*data) for data in best.winners()]
        return out

    def _relationship(self, m, c, plane_name, normal, residual, mid) -> Relationship:
        return Relationship(
            family=self.family,
            axis=f"sym_{plane_name}_{c.entity}",
            label=f"⇔ {plane_name}",
            moving=m,
            targets=(c,),
            residual=residual,
            delta=ConstraintDelta.from_vector(c.co - m.co),
            guide=GuidePlane(point=mid.copy(), normal=normal.copy()),
        )
