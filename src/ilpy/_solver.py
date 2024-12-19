from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from .expressions import Expression
from .solver_backends import Preference, SolverBackend, create_solver_backend

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    import numpy as np

    from ._components import Constraint, Constraints, Objective
    from ._constants import SolverStatus, VariableType
    from .event_data import EventData


@dataclass
class Solution:
    variable_values: Sequence[float]
    objective_value: float
    status: SolverStatus
    time: float
    native_status: Any = None

    def __array__(self) -> np.ndarray:
        import numpy as np

        return np.asarray(self.variable_values)

    def __iter__(self) -> Iterator[float]:
        return iter(self.variable_values)

    def get_value(self) -> float:
        return self.objective_value

    def __getitem__(self, key: int) -> float:
        return self.variable_values[key]

    def __setitem__(self, key: int, value: float) -> None:
        self.variable_values[key] = value  # type: ignore

    def get_status(self) -> str:
        return self.status.name


class Solver:
    def __init__(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: dict[int, VariableType] | None = None,
        preference: Preference = Preference.Any,
    ) -> None:
        vtpes: dict[int, VariableType] = dict(variable_types) if variable_types else {}
        self._backend: SolverBackend = create_solver_backend(preference)
        self._num_variables = num_variables
        self._backend.initialize(num_variables, default_variable_type, vtpes)

    def set_objective(self, objective: Objective | Expression) -> None:
        if isinstance(objective, Expression):
            objective = objective.as_objective()
        self._backend.set_objective(objective)

    def set_constraints(self, constraints: Constraints) -> None:
        self._backend.set_constraints(constraints)

    def add_constraint(self, constraint: Constraint | Expression) -> None:
        if isinstance(constraint, Expression):
            constraint = constraint.as_constraint()
        self._backend.add_constraint(constraint)

    def set_timeout(self, timeout: float) -> None:
        self._backend.set_timeout(timeout)

    def set_optimality_gap(self, gap: float, absolute: bool = False) -> None:
        self._backend.set_optimality_gap(gap, absolute)

    def set_num_threads(self, num_threads: int) -> None:
        self._backend.set_num_threads(num_threads)

    def set_verbose(self, verbose: bool) -> None:
        self._backend.set_verbose(verbose)

    def set_event_callback(self, callback: Callable[[EventData], None] | None) -> None:
        self._backend.set_event_callback(callback)

    def solve(self) -> Solution:
        return self._backend.solve()

    def native_model(self) -> Any:
        return self._backend.native_model()
