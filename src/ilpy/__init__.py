from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ilpy")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"

from ._components import Constraint, Constraints, Objective
from ._constants import Relation, Sense, SolverStatus, VariableType
from ._functional import solve
from ._solver import Solution, Solver
from .expressions import Expression, Variable
from .solver_backends import Preference, SolverBackend

Maximize = Sense.Maximize
Minimize = Sense.Minimize

__all__ = [
    "Constraint",
    "Constraints",
    "Expression",
    "Maximize",
    "Minimize",
    "Objective",
    "Preference",
    "Relation",
    "Sense",
    "Solution",
    "Solver",
    "SolverBackend",
    "SolverStatus",
    "Variable",
    "VariableType",
    "solve",
]
