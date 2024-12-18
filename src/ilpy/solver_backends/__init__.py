from enum import IntEnum, auto

from ._base import SolverBackend

__all__ = ["Preference", "SolverBackend", "create_backend"]


class Preference(IntEnum):
    """Preference for a solver backend."""

    Any = auto()
    Scip = auto()
    Gurobi = auto()


def create_backend(preference: Preference) -> "SolverBackend":
    """Create a solver backend based on the preference."""
    to_try = []
    if preference in (Preference.Any, Preference.Gurobi):
        to_try.append(("_gurobi", "GurobiSolver"))
    elif preference in (Preference.Any, Preference.Scip):
        to_try.append(("_scip", "ScipSolver"))

    for modname, clsname in to_try:
        try:
            mod = __import__(f"ilpy.solver_backends.{modname}", fromlist=[clsname])
            return getattr(mod, clsname)()  # type: ignore [no-any-return]
        except ImportError as e:
            print(e)

    raise ValueError(f"Unknown preference: {preference}")
