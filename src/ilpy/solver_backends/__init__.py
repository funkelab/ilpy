from __future__ import annotations

from contextlib import suppress
from enum import IntEnum, auto
from functools import cache

from ._base import SolverBackend

__all__ = ["Preference", "SolverBackend", "create_solver_backend"]


class Preference(IntEnum):
    """Preference for a solver backend.

    A "full" Gurobi license means one that is *not* the size-limited license
    bundled with the `gurobipy` pip wheel. See
    https://support.gurobi.com/hc/en-us/articles/360051597492

    - `Any`: Use Gurobi if a full license is available, otherwise fall back
      to SCIP. The bundled size-limited license is treated as "no license" to
      avoid silent "Model too large" failures on problems with >2000 variables.
    - `Scip`: Use SCIP. Raises if `pyscipopt` is not installed.
    - `Gurobi`: Use Gurobi; requires a full license. Raises otherwise. Use
      `GurobiRestricted` if you only have the bundled pip license.
    - `GurobiRestricted`: Use Gurobi with whatever license resolves
      (including the bundled size-limited pip license). Suitable for small
      problems (<2000 variables); larger ones will fail at solve time.
    """

    Any = auto()
    Scip = auto()
    Gurobi = auto()
    GurobiRestricted = auto()


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
    if preference in (Preference.Any, Preference.GurobiRestricted):
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
    """Return True if a real (non size-limited) Gurobi license is available.

    Delegates license resolution to gurobipy itself so every documented search
    location is honored — the `GRB_LICENSE_FILE` environment variable, the
    user's home directory, and the platform-specific shared install directory
    (`/opt/gurobi` on Linux, `/Library/gurobi` on macOS, `C:\\gurobi` on
    Windows). See
    https://support.gurobi.com/hc/en-us/articles/360013417211

    The pip/conda `gurobipy` wheel ships with a bundled size-limited license
    (max 2000 variables); it reports `LicenseID == 0`. We treat that case as
    "no license" so callers can fall back to SCIP for larger problems.
    """
    try:
        import gurobipy as gp
    except ImportError:
        return False
    with suppress(Exception):
        # empty=True defers license validation until start()
        with gp.Env(empty=True) as env:
            # silence the startup banner and the "Restricted license" notice
            env.setParam("OutputFlag", 0)
            env.start()
            return int(env.getParam("LicenseID")) != 0
    # no license file found, or license expired
    return False
