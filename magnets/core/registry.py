"""Solver registry and feature-pair dispatcher."""

from __future__ import annotations

from .features import FeaturePool
from .relationship import Relationship
from .solvers.base import SolveContext, Solver

_REGISTRY: list[Solver] = []


def register_solver(solver: Solver) -> None:
    """Append ``solver`` to the global registry."""
    _REGISTRY.append(solver)


def all_solvers() -> list[Solver]:
    """Return a copy of registered solvers."""
    return list(_REGISTRY)


def clear_registry() -> None:
    """Remove all registered solvers (tests)."""
    _REGISTRY.clear()


def dispatch(
    moving: FeaturePool,
    candidates: FeaturePool,
    ctx: SolveContext,
    enabled_families: set[str],
) -> list[Relationship]:
    """Run the enabled solvers on each matching feature-type pair."""
    out: list[Relationship] = []
    for solver in _REGISTRY:
        if solver.family not in enabled_families:
            continue
        mt, ct = solver.feature_types()
        m_feats = moving.by_type(mt)
        c_feats = candidates.by_type(ct)
        if not m_feats or not c_feats:
            continue
        out.extend(solver.solve(m_feats, c_feats, ctx))
    return out
