from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ilpy")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"

from ._components import Constraint, Constraints, Objective
from ._constants import Relation, Sense, SolverStatus, VariableType
from ._functional import solve
from ._solver import Solution, Solver
from .event_data import EventData as EventData
from .event_data import GurobiData as GurobiData
from .event_data import SCIPData as SCIPData
from .expressions import Expression, Variable
from .solver_backends import Preference, SolverBackend

# make enums available at the module level
Any = Preference.Any
Scip = Preference.Scip
Gurobi = Preference.Gurobi
Continuous = VariableType.Continuous
Integer = VariableType.Integer
Binary = VariableType.Binary
Minimize = Sense.Minimize
Maximize = Sense.Maximize
LessEqual = Relation.LessEqual
Equal = Relation.Equal
GreaterEqual = Relation.GreaterEqual

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


def __getattr__(name: str):  # type: ignore
    import warnings

    for suffix in ("Constraint", "Constraints", "Objective", "Solver"):
        if name in {f"Linear{suffix}", f"Quadratic{suffix}"}:
            warnings.warn(
                f"ilpy.{name} is deprecated. Please use ilpy.{suffix} instead",
                DeprecationWarning,
                stacklevel=2,
            )
            return globals()[suffix]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
