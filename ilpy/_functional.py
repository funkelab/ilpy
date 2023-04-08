from typing import Iterable, Literal, Sequence, Tuple

from .expressions import Expression
from .wrapper import Constraint, Objective, Relation, Sense, Solver, VariableType

ConstraintTuple = Tuple[list[float], Relation | str, float]
SenseType = Sense | Literal["minimize", "maximize"]
VariableTypeType = VariableType | Literal["continuous", "binary", "integer"]


def solve(
    objective: Sequence[float] | Expression,
    constraints: Iterable[ConstraintTuple | Expression],
    sense: SenseType = Sense.Minimize,
    variable_type: VariableTypeType = VariableType.Continuous,
    verbose: bool = False,
) -> list[float]:
    if isinstance(sense, str):
        sense = Sense[sense.title()]
    if isinstance(variable_type, str):
        variable_type = VariableType[variable_type.title()]

    if isinstance(objective, Expression):
        obj = objective.as_objective(sense)
    else:
        obj = Objective.from_coefficients(coefficients=objective, sense=sense)

    solver = Solver(len(obj), variable_type)
    solver.set_verbose(verbose)
    solver.set_objective(obj)

    for c in constraints:
        if isinstance(c, Expression):
            const = c.as_constraint()
        else:
            coeff, relation, value = c
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
}
