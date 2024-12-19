from __future__ import annotations

import operator
import os
from typing import TYPE_CHECKING, NamedTuple
from unittest.mock import Mock

import numpy.testing as npt
import pytest

import ilpy
from ilpy.expressions import Expression, Variable

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ilpy._constants import VariableType

# XFAIL if no gurobi not installed or no license found
# (this is the best way I could find to determine this so far)
gu_marks = []
try:
    from ilpy.solver_backends import create_solver_backend

    create_solver_backend(ilpy.Preference.Gurobi)
    import gurobipy as gb

    HAVE_GUROBI = True
except Exception as e:
    gu_marks.append(pytest.mark.xfail(reason=f"Gurobi error: {e}"))
    gb = None
    HAVE_GUROBI = False

PREFS = [
    pytest.param(ilpy.Preference.Scip, id="scip"),
    pytest.param(ilpy.Preference.Gurobi, marks=gu_marks, id="gurobi"),
]


# just a bunch of variables to use in tests
X = [Variable(f"x{i}", index=i) for i in range(10)]


class Case(NamedTuple):
    objective: Sequence[float] | Expression | ilpy.Objective
    constraints: Iterable[tuple | Expression | ilpy.Constraint] = ()
    sense: ilpy.Sense | str = ilpy.Sense.Minimize
    variable_type: VariableType | str = ilpy.VariableType.Continuous
    expectation: Sequence[float] | None = None


CASES = [
    Case(
        objective=[1, 1, 1, 1, 0.5, 1, 1, 1, 1, 1],
        constraints=[([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "=", 1)],
        variable_type=ilpy.VariableType.Binary,
        expectation=[0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    ),
    Case(
        objective=[2, 3],
        constraints=[
            ([3, 2], ilpy.Relation.GreaterEqual, 10),
            ([1, 2], ilpy.Relation.GreaterEqual, 8),
        ],
        expectation=[1, 3.5],
    ),
    Case(
        objective=2 * X[0] + 3 * X[1],
        constraints=[3 * X[0] + 2 * X[1] >= 10, 1 * X[0] + 2 * X[1] >= 8],
        expectation=[1, 3.5],
    ),
    Case(
        objective=X[0] ** 2,
        constraints=[X[0] <= -3],
        expectation=[-3],
    ),
]


@pytest.mark.parametrize("preference", PREFS)
@pytest.mark.parametrize("case", CASES)
def test_solve(preference: ilpy.Preference, case: Case) -> None:
    kwargs = case._asdict()
    expectation = kwargs.pop("expectation")
    mock = Mock()
    solution = ilpy.solve(**kwargs, preference=preference, on_event=mock)
    npt.assert_allclose(solution, expectation)
    # if preference == ilpy.Preference.Scip:
    # assert mock.call_count > 0
    assert all(
        "event_type" in x.args[0] and "backend" in x.args[0]
        for x in mock.call_args_list
    )


@pytest.mark.skipif(gb is None, reason="Gurobipy not installed")
@pytest.mark.parametrize("case", CASES)
def test_gurobipy_solve(case: Case) -> None:
    # just a sanity check to ensure that our solutions match gurobipy's
    kwargs = case._asdict()
    expectation = kwargs.pop("expectation")
    npt.assert_allclose(_gurobipy_solve(**kwargs), expectation)


def _gurobipy_solve(
    objective: list[float],
    constraints: list[tuple[list[float], ilpy.Relation | str, float]],
    sense: ilpy.Sense | int = ilpy.Sense.Minimize,
    verbose: bool = False,
    variable_type: ilpy.VariableType | str = ilpy.VariableType.Continuous,
) -> list[float]:
    """Solve a linear program using Gurobipy.

    This is used for testing purposes only: it uses Gurobipy's API directly
    instead of going through ilpy.

    Examples
    --------
    >>> gurobipy_solve([2, 3], [([3, 2], ">=", 10), ([1, 2], ">=", 8)])
    [1.0, 3.5]
    """
    if isinstance(objective, Expression):
        objective = objective.as_objective().get_coefficients()

    n_vars = len(objective)

    model = gb.Model()
    model.params.OutputFlag = int(verbose)

    # map ilpy variable types to gurobipy variable types
    vtype = {
        ilpy.VariableType.Continuous: gb.GRB.CONTINUOUS,
        ilpy.VariableType.Binary: gb.GRB.BINARY,
        ilpy.VariableType.Integer: gb.GRB.INTEGER,
        gb.GRB.CONTINUOUS: gb.GRB.CONTINUOUS,
        gb.GRB.BINARY: gb.GRB.BINARY,
        gb.GRB.INTEGER: gb.GRB.INTEGER,
    }[variable_type]
    # ilpy uses infinite bounds by default, but Gurobi uses 0 to infinity by default
    x = model.addVars(n_vars, lb=-gb.GRB.INFINITY, vtype=vtype)

    # map ilpy senses to gurobipy senses
    _sense = {
        gb.GRB.MINIMIZE: gb.GRB.MINIMIZE,
        gb.GRB.MAXIMIZE: gb.GRB.MAXIMIZE,
        ilpy.Sense.Minimize: gb.GRB.MINIMIZE,
        ilpy.Sense.Maximize: gb.GRB.MAXIMIZE,
    }[sense]
    objective = sum(objective[i] * x[i] for i in range(n_vars))
    model.setObjective(objective, _sense)

    # map ilpy relations to gurobipy relations
    _op_map = {
        ilpy.Relation.GreaterEqual: operator.ge,
        ilpy.Relation.LessEqual: operator.le,
        ilpy.Relation.Equal: operator.eq,
        ">=": operator.ge,
        "<=": operator.le,
        "=": operator.eq,
    }

    # add constraints to the model
    qcoefs: dict[tuple[int, int], float]
    for c in constraints:
        if isinstance(c, Expression):
            # convert ilpy expressions to gurobipy constraints
            _c = c.as_constraint()
            coefs, qcoefs, relation, val = (
                _c.get_coefficients(),
                _c.get_quadratic_coefficients(),
                _c.get_relation(),
                _c.get_value(),
            )
        else:
            _coefs, relation, val = c
            coefs = dict(enumerate(_coefs))
            qcoefs = {}
        left = sum(lcoef * x[idx] for idx, lcoef in coefs.items())
        for (i, j), qcoef in qcoefs.items():
            left += qcoef * x[i] * x[j]
        model.addConstr(_op_map[relation](left, val))

    model.optimize()
    return [getattr(x[i], "x", 0) for i in range(n_vars)]


@pytest.mark.skipif(os.name == "nt", reason="very slow on windows CI for some reason.")
@pytest.mark.parametrize("preference", PREFS)
def test_non_convex_quadratic(preference: ilpy.Preference) -> None:
    # currently, just a smoke test to make sure we don't crash on solve.
    obj = ilpy.Objective()
    obj.set_quadratic_coefficient(0, 0, -1)  # quadratic term (-x^2)

    solver = ilpy.Solver(1, ilpy.VariableType.Continuous, preference=preference)
    solver.set_objective(obj)

    constraint = ilpy.Constraint()
    constraint.set_coefficient(0, 1)
    constraint.set_value(1)
    solver.add_constraint(constraint)

    # Gurobi will give zeros and SCIP will give something like -9999999987
    assert solver.solve() is not None


def test_solution_indexing() -> None:
    """Test that we can use a Variable instance to index into a solution."""
    solver = ilpy.Solver(5, ilpy.VariableType.Continuous)
    solution = solver.solve()
    x = ilpy.Variable("x", index=0)
    _ = solution[x]  # smoke test
    solution[x] = 2  # can be used to set too
    assert solution[x] == 2


@pytest.mark.parametrize("preference", PREFS)
def test_solve_twice(preference: ilpy.Preference) -> None:
    solver = ilpy.Solver(2, ilpy.VariableType.Integer, preference=preference)
    x1 = ilpy.Variable("x1", index=0)
    x2 = ilpy.Variable("x2", index=1)

    solver.set_objective((x1 + x2).as_objective(ilpy.Maximize))

    c0 = ilpy.Constraints()
    c0.add(x1 + x2 <= 10)
    c0.add(2 * x1 + 3 * x2 >= 12)
    c0.add(x1 - x2 <= 5)

    c1 = ilpy.Constraints()
    c1.add(x1 + x2 <= 10)
    c1.add(2 * x1 + 3 * x2 >= 12)
    c1.add(x1 - x2 >= 5)

    # initial solve
    solver.set_constraints(c0)
    solution = solver.solve()
    assert list(solution) == [7, 3]
    assert solution.get_value() == 10

    # add a constraint and check that the solution has changed
    solver.set_constraints(c1)
    solution = solver.solve()
    assert list(solution) != [7, 3]
