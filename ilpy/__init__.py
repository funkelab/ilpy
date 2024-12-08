from typing import TYPE_CHECKING

from . import wrapper
from ._functional import solve
from .expressions import Expression, Variable
from .wrapper import *  # noqa: F403

if TYPE_CHECKING:
    from .event_data import EventData as EventData
    from .event_data import GurobiData as GurobiData
    from .event_data import SCIPData as SCIPData

__version__ = "0.4.1"
__all__ = [  # noqa: F405
    "Any",
    "Binary",
    "Constraint",
    "Constraint",
    "Constraints",
    "Continuous",
    "Cplex",
    "Equal",
    "Expression",
    "GreaterEqual",
    "Gurobi",
    "Integer",
    "LessEqual",
    "Maximize",
    "Minimize",
    "Objective",
    "Preference",
    "Relation",
    "Scip",
    "Sense",
    "Solution",
    "Solver",
    "Solver",
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
            return getattr(wrapper, suffix)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
