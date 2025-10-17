from __future__ import annotations

import os
from enum import IntEnum, auto
from functools import cache
from pathlib import Path

from ._base import SolverBackend

__all__ = ["Preference", "SolverBackend", "create_solver_backend"]


class Preference(IntEnum):
    """Preference for a solver backend."""

    Any = auto()
    Scip = auto()
    Gurobi = auto()
    GurobiUnlicensed = auto()


def create_solver_backend(preference: Preference | str) -> SolverBackend:
    """Create a solver backend based on the preference."""
    if not isinstance(preference, Preference):
        preference = Preference[str(preference).title()]

    to_try = []
    if preference in (Preference.Any, Preference.Gurobi):
        if _have_gurobi_license():
            to_try.append(("_gurobi", "GurobiSolver"))
        elif preference == Preference.Gurobi:
            raise RuntimeError("Gurobi license is not available. ")
    if preference in (Preference.Any, Preference.Scip):
        to_try.append(("_scip", "ScipSolver"))
    if preference in (Preference.Any, Preference.GurobiUnlicensed):
        to_try.append(("_gurobi", "GurobiSolver"))

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


@cache
def _have_gurobi_license() -> bool:
    """Check if Gurobi license is available.

    This assumes that the license file is located as described in the Gurobi docs:
    https://support.gurobi.com/hc/en-us/articles/360013417211-Where-do-I-place-the-Gurobi-license-file-gurobi-lic
    """
    license_file = Path.home() / "gurobi.lic"
    if license_file.exists():
        return True
    if (env_file := os.getenv("GRB_LICENSE_FILE", "")) and Path(env_file).exists():
        return True
    return False
