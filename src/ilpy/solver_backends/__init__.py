from __future__ import annotations

from enum import IntEnum, auto

from ._base import SolverBackend

__all__ = ["Preference", "SolverBackend", "create_solver_backend"]


class Preference(IntEnum):
    """Preference for a solver backend."""

    Any = auto()
    Scip = auto()
    Gurobi = auto()


def create_solver_backend(preference: Preference | str) -> SolverBackend:
    """Create a solver backend based on the preference."""
    if not isinstance(preference, Preference):
        preference = Preference[str(preference).title()]

    to_try = []
    if preference in (Preference.Any, Preference.Gurobi):
        to_try.append(("_gurobi", "GurobiSolver"))
    if preference in (Preference.Any, Preference.Scip):
        to_try.append(("_scip", "ScipSolver"))

    errors: list[tuple[str, BaseException]] = []
    for modname, clsname in to_try:
        import_mod = f"ilpy.solver_backends.{modname}"
        try:
            mod = __import__(import_mod, fromlist=[clsname])
            cls = getattr(mod, clsname)
            backend = cls()
            assert isinstance(backend, SolverBackend)
            return backend
        except Exception as e:  # pragma: no cover
            errors.append((f"{import_mod}::{clsname}", e))

    raise RuntimeError(  # pragma: no cover
        "Failed to create a solver backend. Tried:\n\n"
        + "\n".join(f"- {name}:\n    {e}" for name, e in errors)
    )
