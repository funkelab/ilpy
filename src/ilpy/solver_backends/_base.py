from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ilpy._components import Constraint, Constraints, Objective
    from ilpy._constants import VariableType
    from ilpy._solver import Solution


class SolverBackend(ABC):
    @abstractmethod
    def initialize(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: Mapping[int, VariableType],
    ) -> None: ...

    @abstractmethod
    def set_objective(self, objective: Objective) -> None: ...

    @abstractmethod
    def set_constraints(self, constraints: Constraints) -> None: ...

    @abstractmethod
    def add_constraint(self, constraint: Constraint) -> None: ...

    @abstractmethod
    def set_timeout(self, timeout: float) -> None: ...

    @abstractmethod
    def set_optimality_gap(self, gap: float, absolute: bool) -> None: ...

    @abstractmethod
    def set_num_threads(self, num_threads: int) -> None: ...

    @abstractmethod
    def set_verbose(self, verbose: bool) -> None: ...

    @abstractmethod
    def set_event_callback(
        self, callback: Callable[[Mapping[str, float | str]], None] | None
    ) -> None: ...

    @abstractmethod
    def solve(self) -> Solution: ...

    @abstractmethod
    def native_model(self) -> Any: ...
