"""Marker-family solver implementations (no bpy)."""

from ..registry import register_solver
from .alignment import AlignmentSolver, EdgeAlignmentSolver
from .collinear import CollinearSolver
from .concentric import ConcentricSolver
from .coplanar import CoplanarSolver
from .distribution import DistributionSolver
from .equal_size import EqualSizeSolver
from .midpoint import MidpointSolver
from .parallel import DirectionParallelSolver, ParallelSolver
from .spacing import SpacingSolver
from .symmetry import SymmetrySolver
from .tangency import SurfaceTangencySolver, TangencySolver

for _solver in (
    AlignmentSolver(),
    EdgeAlignmentSolver(),
    SpacingSolver(),
    DistributionSolver(),
    EqualSizeSolver(),
    MidpointSolver(),
    TangencySolver(),
    SurfaceTangencySolver(),
    ParallelSolver(),
    DirectionParallelSolver(),
    CollinearSolver(),
    CoplanarSolver(),
    ConcentricSolver(),
    SymmetrySolver(),
):
    register_solver(_solver)
