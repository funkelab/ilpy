from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from .expressions import Expression
from .solver_backends import Preference, SolverBackend, create_solver_backend

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    import numpy as np
    import numpy.typing as npt

    from ._components import Constraint, Constraints, Objective
    from ._constants import SolverStatus, VariableType
    from .event_data import EventData


@dataclass
class Solution:
    """The result of solving an optimization problem.

    Attributes
    ----------
    variable_values : Sequence[float]
        The values assigned to each variable by the solver.
    objective_value : float
        The value of the objective at the returned solution.
    status : SolverStatus
        Normalized status reported by the solver.
    time : float
        Wall-clock time (seconds) spent solving.
    native_status : Any
        The backend-specific status object, for callers who need more detail
        than `SolverStatus` provides.
    """

    variable_values: Sequence[float]
    objective_value: float
    status: SolverStatus
    time: float
    native_status: Any = None

    def __array__(
        self, dtype: npt.DTypeLike | None = None, copy: bool | None = None
    ) -> np.ndarray:
        import numpy as np

        return np.asarray(self.variable_values, dtype=dtype, copy=copy)

    def __iter__(self) -> Iterator[float]:
        return iter(self.variable_values)

    def get_value(self) -> float:
        """Return the objective value at this solution."""
        return self.objective_value

    def __getitem__(self, key: int) -> float:
        return self.variable_values[key]

    def __setitem__(self, key: int, value: float) -> None:
        self.variable_values[key] = value  # type: ignore

    def get_status(self) -> str:
        """Return the solver status as a string (the enum member name)."""
        return self.status.name


class Solver:
    """High-level wrapper around an ILP solver backend."""

    def __init__(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: dict[int, VariableType] | None = None,
        preference: Preference = Preference.Any,
    ) -> None:
        """Create a solver with `num_variables` decision variables.

        Parameters
        ----------
        num_variables : int
            The number of decision variables in the problem.
        default_variable_type : VariableType
            The type used for variables not listed in `variable_types`.
        variable_types : dict[int, VariableType], optional
            Per-variable overrides for the default variable type.
        preference : Preference
            Backend preference.  `Preference.Any` picks the first available.
        """
        vtpes: dict[int, VariableType] = dict(variable_types) if variable_types else {}
        self._backend: SolverBackend = create_solver_backend(preference)
        self._num_variables = num_variables
        self._backend.initialize(num_variables, default_variable_type, vtpes)

    def set_objective(self, objective: Objective | Expression) -> None:
        """Set the objective, converting from an `Expression` if needed."""
        if isinstance(objective, Expression):
            objective = objective.as_objective()
        self._backend.set_objective(objective)

    def set_constraints(self, constraints: Constraints) -> None:
        """Replace the current constraint set."""
        self._backend.set_constraints(constraints)

    def add_constraint(self, constraint: Constraint | Expression) -> None:
        """Add a single constraint (or an `Expression` convertible to one)."""
        if isinstance(constraint, Expression):
            constraint = constraint.as_constraint()
        self._backend.add_constraint(constraint)

    def set_timeout(self, timeout: float) -> None:
        """Set a wall-clock time limit (in seconds) for solving."""
        self._backend.set_timeout(timeout)

    def set_optimality_gap(self, gap: float, absolute: bool = False) -> None:
        """Set the optimality gap at which the solver may stop.

        If `absolute` is True, `gap` is the absolute gap; otherwise it is
        interpreted as a relative gap.
        """
        self._backend.set_optimality_gap(gap, absolute)

    def set_num_threads(self, num_threads: int) -> None:
        """Set the number of threads the backend may use."""
        self._backend.set_num_threads(num_threads)

    def set_verbose(self, verbose: bool) -> None:
        """Enable or disable solver log output."""
        self._backend.set_verbose(verbose)

    def set_event_callback(self, callback: Callable[[EventData], None] | None) -> None:
        """Set (or clear) a callback invoked on backend progress events."""
        self._backend.set_event_callback(callback)

    def solve(self) -> Solution:
        """Solve the problem and return a `Solution`."""
        return self._backend.solve()

    def native_model(self) -> Any:
        """Return the backend's native model object (e.g. a gurobipy Model)."""
        return self._backend.native_model()
