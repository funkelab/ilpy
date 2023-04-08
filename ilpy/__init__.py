from . import wrapper
from .wrapper import *  # noqa: F403

__version__ = "0.2.3"
__all__ = [  # noqa: F405
    "Any",
    "Binary",
    "Constraint",
    "Constraint",
    "Constraints",
    "Continuous",
    "Cplex",
    "Equal",
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
    "VariableType",
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
