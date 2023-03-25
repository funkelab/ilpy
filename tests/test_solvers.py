import pytest

import ilpy
from ilpy.expressions import Constant, Expression, Variable

# XFAIL if no gurobi not installed or no license found
# (this is the best way I could find to determine this so far)
marks = []
try:
    ilpy.LinearSolver(0, ilpy.VariableType.Binary, None, ilpy.Preference.Gurobi)
except RuntimeError:
    marks.append(pytest.mark.xfail(reason="Gurobi missing or no license found"))


@pytest.mark.parametrize("as_expression", [True, False], ids=["as_expr", "as_constr"])
@pytest.mark.parametrize(
    "preference",
    [ilpy.Preference.Scip, pytest.param(ilpy.Preference.Gurobi, marks=marks)],
)
def test_simple_solver(preference: ilpy.Preference, as_expression: bool) -> None:
    num_vars = 10
    special_var = 5

    solver = ilpy.LinearSolver(
        num_vars,
        ilpy.VariableType.Binary,
        {special_var: ilpy.VariableType.Continuous},
        preference,
    )

    _e: Expression
    # objective function
    if as_expression:
        # note: the Constant(0) here is only to satisfy mypy... it would work without
        _e = sum((Variable(str(i), index=i) for i in range(num_vars)), Constant(0))
        _e += 0.5 * Variable(str(special_var), index=special_var)
        objective = _e.as_objective()
    else:
        objective = ilpy.LinearObjective()
        for i in range(num_vars):
            objective.set_coefficient(i, 1.0)
        objective.set_coefficient(special_var, 0.5)

    # constraints
    if as_expression:
        _e = sum((Variable(str(i), index=i) for i in range(num_vars)), Constant(0))
        constraint = (_e == 1).as_constraint()
    else:
        constraint = ilpy.LinearConstraint()
        for i in range(num_vars):
            constraint.set_coefficient(i, 1.0)
        constraint.set_relation(ilpy.Relation.Equal)
        constraint.set_value(1.0)

    solver.set_objective(objective)
    solver.add_constraint(constraint)

    solution, _ = solver.solve()

    assert solution[5] == 1
