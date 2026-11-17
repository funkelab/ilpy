from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Literal

from ._components import Constraint, Objective
from ._constants import Relation, Sense, VariableType
from ._solver import Solution, Solver
from .expressions import Expression
from .solver_backends import Preference

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from .event_data import EventData

    ConstraintTuple = tuple[list[float], Relation | str, float]
    SenseType = Sense | Literal["minimize", "maximize"]
    VariableTypeType = VariableType | Literal["continuous", "binary", "integer"]
    PreferenceType = (
        Preference | Literal["any", "scip", "gurobi", "gurobirestricted", "cuopt"]
    )


def solve(
    objective: Sequence[float] | Expression | Objective,
    constraints: Iterable[ConstraintTuple | Expression | Constraint],
    sense: SenseType | None = None,
    variable_type: VariableTypeType = VariableType.Continuous,
    verbose: bool = False,
    preference: PreferenceType = Preference.Any,
    on_event: Callable[[EventData], None] | None = None,
) -> Solution:
    """Solve an objective subject to constraints.

    This is a functional interface to the solver. It creates a solver instance
    and sets the objective and constraints, then solves the problem and returns
    the solution.

    Parameters
    ----------
    objective : Sequence[float] | Expression | Objective
        The objective to solve.  If a sequence of floats is provided, it is
        interpreted as the coefficients of the objective. For example, the objective
        2x + 3y would be provided as [2, 3].
        Alternatively, an [`ilpy.Expression`][] or [`ilpy.Objective`][] can be provided.
    constraints : Iterable[ConstraintTuple  |  Expression  |  Constraint]
        The constraints to satisfy.  May be provided as a sequence of Expression or
        Constraint objects, or as a sequence of tuples of the form
        (coefficients, relation, value), where coefficients is a sequence of floats,
        relation is an [`ilpy.Relation`][] or a string in {"<=", ">=", "="}, and value
        is a float.  For example, the constraint 2x + 3y <= 5 would be provided as
        `([2, 3], Relation.LessEqual, 5)`.
    sense : Sense | Literal["minimize", "maximize"]
        The sense of the objective, either `Sense.Minimize` or `Sense.Maximize`.
        Alternatively, a string in {"minimize", "maximize"} can be provided.
        By default, `Sense.Minimize` (or the sense of `objective`, if it is an
        `Objective`).
    variable_type : VariableType | Literal["continuous", "binary", "integer"]
        The type of the variables, either an [`ilpy.VariableType`][], or a string in
        {"continuous", "binary", "integer"}.  By default, `VariableType.Continuous`.
    verbose : bool, optional
        Whether to print the solver output, by default `False`.
    preference : Preference | str
        Backend preference, either an [`ilpy.Preference`][] or its (case-insensitive)
        name, e.g. "scip" or "cuopt".  By default, `Preference.Any`.
    on_event : Callable[[EventData], None], optional
        A callback function that is called when an event occurs, by default None. The
        callback function should accept a dict which will contain statics about the
        solving or presolving process. You can import `ilpy.EventData` from ilpy and use
        it to provide dict key hints in your IDE, but `EventData` is not available at
        runtime. See SCIP and Gurobi documentation for details what each value means.

        For example

        ```python
        import ilpy

        if TYPE_CHECKING:
            from ilpy import EventData


        def callback(data: EventData) -> None:
            if data["backend"] == "gurobi" and data["event_type"] == "MIP":
                print(data["gap"])


        ilpy.solve(..., on_event=callback)
        ```

    Returns
    -------
    Solution
        The solution to the problem.
    """
    if isinstance(sense, str):
        sense = Sense[sense.title()]
    if isinstance(variable_type, str):
        variable_type = VariableType[variable_type.title()]

    if isinstance(objective, Expression):
        obj = objective.as_objective(sense or Sense.Minimize)
    elif isinstance(objective, Objective):
        obj = objective
        if sense is not None:
            obj = copy.copy(objective)  # don't modify the caller's objective
            obj.set_sense(sense)
    else:
        obj = Objective.from_coefficients(
            coefficients=objective, sense=sense or Sense.Minimize
        )

    consts: list[Constraint] = []
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
        consts.append(const)

    # constraints may reference variables that don't appear in the objective
    num_variables = len(obj)
    for const in consts:
        for i in const.get_coefficients():
            num_variables = max(num_variables, i + 1)
        for i, j in const.get_quadratic_coefficients():
            num_variables = max(num_variables, i + 1, j + 1)

    solver = Solver(num_variables, variable_type, preference=preference)
    solver.set_verbose(verbose)
    solver.set_objective(obj)
    for const in consts:
        solver.add_constraint(const)

    solver.set_event_callback(on_event)
    solution = solver.solve()
    return solution


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
