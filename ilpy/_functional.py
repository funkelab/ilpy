from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable, Literal, Mapping, Sequence, Tuple

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
    on_event: Callable[[Mapping], None] | None = None,
) -> list[float]:
    """Solve an objective subject to constraints.

    Parameters
    ----------
    objective : Sequence[float] | Expression | Objective
        The objective to solve.  If a sequence of floats is provided, it is
        interpreted as the coefficients of the objective. For example, the objective
        2x + 3y would be provided as [2, 3].
        Alternatively, an `ilpy.Expression` or `ilpy.Objective` can be provided.
    constraints : Iterable[ConstraintTuple  |  Expression  |  Constraint]
        The constraints to satisfy.  May be provided as a sequence of Expression or
        Constraint objects, or as a sequence of tuples of the form
        (coefficients, relation, value), where coefficients is a sequence of floats,
        relation is an `ilpy.Relation` or a string in {"<=", ">=", "="}, and value is a
        float.  For example, the constraint 2x + 3y <= 5 would be provided as
        `([2, 3], Relation.LessEqual, 5)`.
    sense : Sense | Literal["minimize", "maximize"]
        The sense of the objective, either `Sense.Minimize` or `Sense.Maximize`.
        Alternatively, a string in {"minimize", "maximize"} can be provided.
        By default, `Sense.Minimize`.
    variable_type : VariableType | Literal["continuous", "binary", "integer"]
        The type of the variables, either an `ilpy.VariableType`, or a string in
        {"continuous", "binary", "integer"}.  By default, `VariableType.Continuous`.
    verbose : bool, optional
        Whether to print the solver output, by default False.
    preference : Preference | Literal["any", "cplex", "gurobi", "scip"]
        Backend preference, either an `ilpy.Preference` or a string in
        {"any", "cplex", "gurobi", "scip"}.  By default, `Preference.Any`.
    on_event : Callable[[Mapping], None], optional
        A callback function that is called when an event occurs, by default None.
        The callback function should accept a dict which will contain event
        metadata.

    Returns
    -------
    list[float]
        The solution to the objective.
    """
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

    solver.set_event_callback(on_event)
    solution = solver.solve()
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
