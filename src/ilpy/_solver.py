from collections.abc import Mapping
from typing import Callable, NamedTuple, Sequence, SupportsIndex

from ._components import Constraint, Constraints, Objective
from ._constants import Preference, VariableType
from .expressions import Expression
from .solver_backends import SolverBackend, create_backend


class Solution(NamedTuple):
    variable_values: Sequence[float]
    objective_value: float
    status: str
    time: float


class Solver:
    def __init__(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: dict[int, VariableType] | None = None,
        preference: Preference = Preference.Any,
    ) -> None:
        vtpes: dict[int, VariableType] = dict(variable_types) if variable_types else {}
        self._backend: SolverBackend = create_backend(preference)
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

    def set_event_callback(
        self, callback: Callable[[Mapping[str, float | str]], None] | None
    ) -> None:
        self._backend.set_event_callback(callback)

    def solve(self) -> Solution:
        return self._backend.solve()
