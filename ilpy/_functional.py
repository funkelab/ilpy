from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Literal, Sequence, Tuple

from .expressions import Expression
from .wrapper import (
    Constraint,
    Objective,
    Preference,
    Relation,
    Sense,
    Solver,
    VariableType,
)

if TYPE_CHECKING:
    ConstraintTuple = Tuple[list[float], Relation | str, float]
    SenseType = Sense | Literal["minimize", "maximize"]
    VariableTypeType = VariableType | Literal["continuous", "binary", "integer"]
    PreferenceType = Preference | Literal["any", "cplex", "gurobi", "scip"]


def solve(
    objective: Sequence[float] | Expression | Objective,
    constraints: Iterable[ConstraintTuple | Expression | Constraint],
    sense: SenseType = Sense.Minimize,
    variable_type: VariableTypeType = VariableType.Continuous,
    verbose: bool = False,
    preference: PreferenceType = Preference.Any,
) -> list[float]:
    if isinstance(sense, str):
        sense = Sense[sense.title()]
    if isinstance(variable_type, str):
        variable_type = VariableType[variable_type.title()]
    if isinstance(preference, str):
        preference = Preference[preference.title()]

    if isinstance(objective, Expression):
        obj = objective.as_objective(sense)
    elif isinstance(objective, Objective):
        obj = objective
    else:
        obj = Objective.from_coefficients(coefficients=objective, sense=sense)

    solver = Solver(len(obj), variable_type, preference=preference)
    solver.set_verbose(verbose)
    solver.set_objective(obj)

    for constraint in constraints:
        if isinstance(constraint, Expression):
            const = constraint.as_constraint()
        elif isinstance(constraint, Constraint):
            const = constraint
        else:
            coeff, relation, value = constraint
            const = Constraint.from_coefficients(
                coefficients=coeff, relation=_op_map[relation], value=value
            )
        solver.add_constraint(const)

    solution, _ = solver.solve()
    return list(solution)  # type: ignore


_op_map = {
    Relation.GreaterEqual: Relation.GreaterEqual,
    Relation.LessEqual: Relation.LessEqual,
    Relation.Equal: Relation.Equal,
    ">=": Relation.GreaterEqual,
    "<=": Relation.LessEqual,
    "=": Relation.Equal,
    "==": Relation.Equal,
    "GreaterEqual": Relation.GreaterEqual,
    "LessEqual": Relation.LessEqual,
    "Equal": Relation.Equal,
}
