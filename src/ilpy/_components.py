from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, SupportsIndex

from ilpy._constants import Sense

from ._constants import Relation
from .expressions import Expression

if TYPE_CHECKING:
    from ._solver import Solution

    LinearCoeffs = Sequence[float] | Mapping[int, float]
    QCoeffs = Mapping[tuple[int, int], float] | Iterable[tuple[tuple[int, int], float]]


class Constraint:
    def __init__(self) -> None:
        self._coefs: dict[int, float] = {}
        self._quad_coefs: dict[tuple[int, int], float] = {}
        self._relation: Relation = Relation.LessEqual
        self._value: float = 0.0

    def set_coefficient(self, i: SupportsIndex, value: float) -> None:
        if value == 0:
            self._coefs.pop(int(i), None)
        else:
            self._coefs[int(i)] = value

    def get_coefficients(self) -> Mapping[int, float]:
        return MappingProxyType(self._coefs)

    def set_quadratic_coefficient(
        self, i: SupportsIndex, j: SupportsIndex, value: float
    ) -> None:
        key = (int(i), int(j))
        if value == 0:
            self._quad_coefs.pop(key, None)
        else:
            self._quad_coefs[key] = value

    def get_quadratic_coefficients(self) -> Mapping[tuple[int, int], float]:
        return MappingProxyType(self._quad_coefs)

    def set_relation(self, relation: Relation) -> None:
        self._relation = relation

    def get_relation(self) -> Relation:
        return self._relation

    def set_value(self, value: float) -> None:
        self._value = value

    def get_value(self) -> float:
        return self._value

    def is_violated(self, solution: Solution) -> bool:
        total = sum(coef * solution[var] for var, coef in self._coefs.items())
        if self._relation == Relation.LessEqual:
            return total > self._value
        elif self._relation == Relation.GreaterEqual:
            return total < self._value
        elif self._relation == Relation.Equal:
            return total != self._value
        return False

    @classmethod
    def from_coefficients(
        cls,
        coefficients: LinearCoeffs = (),
        quadratic_coefficients: QCoeffs = (),
        relation: Relation = Relation.LessEqual,
        value: float = 0,
    ) -> Constraint:
        constraint = cls()
        iter_coeffs = (
            coefficients.items()
            if isinstance(coefficients, Mapping)
            else enumerate(coefficients)
        )
        for i, coeff in iter_coeffs:
            constraint.set_coefficient(i, coeff)
        iter_quadratic_coeffs = (
            quadratic_coefficients.items()
            if isinstance(quadratic_coefficients, Mapping)
            else quadratic_coefficients
        )
        for (i, j), coeff in iter_quadratic_coeffs:
            constraint.set_quadratic_coefficient(i, j, coeff)

        constraint.set_relation(relation)
        constraint.set_value(value)
        return constraint


class Constraints:
    def __init__(self) -> None:
        self._constraints: list[Constraint] = []

    def clear(self) -> None:
        self._constraints.clear()

    def add(self, constraint: Constraint | Expression) -> None:
        if isinstance(constraint, Expression):
            self._constraints.append(constraint.as_constraint())
        else:
            self._constraints.append(constraint)

    def add_all(self, constraints: Constraints) -> None:
        self._constraints.extend(constraints._constraints)

    def __len__(self) -> int:
        return len(self._constraints)

    def __iter__(self) -> Iterator[Constraint]:
        return iter(self._constraints)


class Objective:
    def __init__(self, size: int = 0) -> None:
        self._sense = Sense.Minimize
        self._constant = 0.0
        self._coeffs: list[float] = []
        self._quad_coeffs: dict[tuple[int, int], float] = {}

    def set_constant(self, value: float) -> None:
        self._constant = value

    def get_constant(self) -> float:
        return self._constant

    def resize(self, size: int) -> None:
        """Resize the objective function. New coefficients are set to 0."""
        if size < 0:
            raise ValueError("Size must be non-negative.")
        current_size = len(self)
        if current_size < size:
            self._coeffs.extend([0] * (size - current_size))
        elif current_size > size:
            self._coeffs = self._coeffs[:size]

    def set_coefficient(self, i: SupportsIndex, value: float) -> None:
        i = int(i)
        if i >= len(self):
            self.resize(i + 1)
        self._coeffs[i] = value

    def get_coefficients(self) -> list[float]:
        return list(self._coeffs)

    def __iter__(self) -> Iterator[float]:
        return iter(self._coeffs)

    def set_quadratic_coefficient(
        self, i: SupportsIndex, j: SupportsIndex, value: float
    ) -> None:
        i, j = int(i), int(j)
        if i >= len(self) or j >= len(self):
            self.resize(max(i, j) + 1)
        if value == 0:
            self._quad_coeffs.pop((i, j), None)
        else:
            self._quad_coeffs[(i, j)] = value

    def get_quadratic_coefficients(self) -> Mapping[tuple[int, int], float]:
        return MappingProxyType(self._quad_coeffs)

    def set_sense(self, sense: Sense) -> None:
        self._sense = sense

    def get_sense(self) -> Sense:
        return self._sense

    def __len__(self) -> int:
        return len(self._coeffs)

    @classmethod
    def from_coefficients(
        cls,
        coefficients: LinearCoeffs = (),
        quadratic_coefficients: QCoeffs = (),
        constant: float = 0,
        sense: Sense = Sense.Minimize,
    ) -> Objective:
        obj = cls()
        iter_coeffs = (
            coefficients.items()
            if isinstance(coefficients, Mapping)
            else enumerate(coefficients)
        )
        for i, coeff in iter_coeffs:
            obj.set_coefficient(i, coeff)
        iter_quadratic_coeffs = (
            quadratic_coefficients.items()
            if isinstance(quadratic_coefficients, Mapping)
            else quadratic_coefficients
        )
        for (i, j), coeff in iter_quadratic_coeffs:
            obj.set_quadratic_coefficient(i, j, coeff)

        obj.set_constant(constant)
        obj.set_sense(sense)
        return obj
