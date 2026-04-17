from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ilpy._components import Constraint, Constraints, Objective
    from ilpy._constants import VariableType
    from ilpy._solver import Solution
    from ilpy.event_data import EventData


class SolverBackend(ABC):
    """Abstract base class implemented by each concrete solver backend."""

    def __init__(self) -> None:
        self._event_callback: Callable[[EventData], None] | None = None

    def set_event_callback(self, callback: Callable[[EventData], None] | None) -> None:
        """Set (or clear) a callback invoked on solver progress events."""
        self._event_callback = callback

    def emit_event_data(self, data: EventData) -> None:
        """Dispatch `data` to the registered event callback (no-op if none)."""
        if self._event_callback:
            self._event_callback(data)

    @abstractmethod
    def initialize(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: Mapping[int, VariableType],
    ) -> None:
        """Initialize the backend with decision variables and their types."""

    @abstractmethod
    def set_objective(self, objective: Objective) -> None:
        """Set the objective function for the problem."""

    @abstractmethod
    def set_constraints(self, constraints: Constraints) -> None:
        """Replace the backend's current constraint set."""

    @abstractmethod
    def add_constraint(self, constraint: Constraint) -> None:
        """Add a single constraint to the problem."""

    @abstractmethod
    def set_timeout(self, timeout: float) -> None:
        """Set the wall-clock time limit (in seconds) for solving."""

    @abstractmethod
    def set_optimality_gap(self, gap: float, absolute: bool) -> None:
        """Set the optimality gap (absolute or relative) for early termination."""

    @abstractmethod
    def set_num_threads(self, num_threads: int) -> None:
        """Set the number of threads the backend may use."""

    @abstractmethod
    def set_verbose(self, verbose: bool) -> None:
        """Enable or disable backend log output."""

    @abstractmethod
    def solve(self) -> Solution:
        """Solve the problem and return a `Solution`."""

    @abstractmethod
    def native_model(self) -> Any:
        """Return the underlying native model object for this backend."""
