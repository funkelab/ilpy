from enum import IntEnum, auto
from typing import TYPE_CHECKING, Iterable, Mapping, Sequence

if TYPE_CHECKING:
    LinearCoeffs = Sequence[float] | Mapping[int, float]
    QCoeffs = Mapping[tuple[int, int], float] | Iterable[tuple[tuple[int, int], float]]

class Preference(IntEnum):
    Any = auto()
    Scip = auto()
    Gurobi = auto()
    Cplex = auto()

class VariableType(IntEnum):
    Continuous = auto()
    Integer = auto()
    Binary = auto()

class Sense(IntEnum):
    Minimize = auto()
    Maximize = auto()

class Relation(IntEnum):
    LessEqual = auto()
    Equal = auto()
    GreaterEqual = auto()

# cython appears to make these available as module-level constants as well
Any = Preference.Any
Scip = Preference.Scip
Gurobi = Preference.Gurobi
Cplex = Preference.Cplex

Continuous = VariableType.Continuous
Integer = VariableType.Integer
Binary = VariableType.Binary

Minimize = Sense.Minimize
Maximize = Sense.Maximize

LessEqual = Relation.LessEqual
Equal = Relation.Equal
GreaterEqual = Relation.GreaterEqual

class Solution:
    def __init__(self, size: int) -> None: ...
    def __len__(self) -> int: ...
    def __getitem__(self, i: int) -> float: ...
    def __setitem__(self, i: int, value: float) -> None: ...
    def resize(self, size: int) -> None: ...
    def get_value(self) -> float: ...
    def set_value(self, value: float) -> None: ...

class Objective:
    def __init__(self, size: int = 0) -> None: ...
    def set_constant(self, value: float) -> None: ...
    def get_constant(self) -> float: ...
    def set_coefficient(self, i: int, value: float) -> None: ...
    def get_coefficients(self) -> list[float]: ...
    def set_quadratic_coefficient(self, i: int, j: int, value: float) -> None: ...
    def get_quadratic_coefficients(self) -> dict[tuple[int, int], float]: ...
    def set_sense(self, sense: Sense) -> None: ...
    def get_sense(self) -> Sense: ...
    def resize(self, size: int) -> None: ...
    def __len__(self) -> int: ...
    @classmethod
    def from_coefficients(
        cls,
        coefficients: LinearCoeffs = (),
        quadratic_coefficients: QCoeffs = (),
        constant: float = 0,
        sense: Sense = Sense.Minimize,
    ) -> Objective: ...

class Constraint:
    def __init__(self) -> None: ...
    def set_coefficient(self, i: int, value: float) -> None: ...
    def get_coefficients(self) -> dict[int, float]: ...
    def set_quadratic_coefficient(self, i: int, j: int, value: float) -> None: ...
    def get_quadratic_coefficients(self) -> dict[tuple[int, int], float]: ...
    def set_relation(self, relation: Relation) -> None: ...
    def get_relation(self) -> Relation: ...
    def set_value(self, value: float) -> None: ...
    def get_value(self) -> float: ...
    def is_violated(self, solution: Solution) -> bool: ...
    @classmethod
    def from_coefficients(
        cls,
        coefficients: LinearCoeffs = (),
        quadratic_coefficients: QCoeffs = (),
        relation: Relation = Relation.LessEqual,
        value: float = 0,
    ) -> Constraint: ...

class Constraints:
    def __init__(self) -> None: ...
    def clear(self) -> None: ...
    def add(self, constraint: Constraint) -> None: ...
    def add_all(self, constraints: Constraints) -> None: ...
    def __len__(self) -> int: ...

class Solver:
    def __init__(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: dict[int, VariableType] | None = None,
        preference: Preference = Preference.Any,
    ) -> None: ...
    def set_objective(self, objective: Objective) -> None: ...
    def set_constraints(self, constraints: Constraints) -> None: ...
    def add_constraint(self, constraint: Constraint) -> None: ...
    def set_timeout(self, timeout: float) -> None: ...
    def set_optimality_gap(self, gap: float, absolute: bool = False) -> None: ...
    def set_num_threads(self, num_threads: int) -> None: ...
    def set_verbose(self, verbose: bool) -> None: ...
    def solve(self) -> tuple[Solution, str]: ...
