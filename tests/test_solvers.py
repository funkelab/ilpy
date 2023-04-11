from __future__ import annotations

import operator
import os
from typing import Iterable, NamedTuple, Sequence

import ilpy
import numpy.testing as npt
import pytest
from ilpy.expressions import Expression, Variable
from ilpy.wrapper import VariableType

# XFAIL if no gurobi not installed or no license found
# (this is the best way I could find to determine this so far)
gu_marks = []
try:
    ilpy.Solver(0, ilpy.VariableType.Binary, None, ilpy.Preference.Gurobi)
    HAVE_GUROBI = True
    try:
        import gurobipy as gb
    except ImportError:
        if os.getenv("CI"):
            raise ImportError("Gurobipy not installed, but required for CI") from None
        gb = None
except RuntimeError:
    gu_marks.append(pytest.mark.xfail(reason="Gurobi missing or no license found"))
    gb = None
    HAVE_GUROBI = False

PREFS = [
    pytest.param(ilpy.Preference.Scip, id="scip"),
    pytest.param(ilpy.Preference.Gurobi, marks=gu_marks, id="gurobi"),
]


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
    # abort trap at the moment
    # Case(
    #     objective=-X[0] ** 2,
    #     constraints=[X[0] <= -3],
    #     expectation=[-3],
    # ),
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
    npt.assert_allclose(ilpy.solve(**kwargs, preference=preference), expectation)


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
    >>> gurobipy_solve([2,3], [([3,2], '>=', 10), ([1,2], '>=', 8)])
    [1.0, 3.5]
    """
    _obj = objective
    if isinstance(objective, Expression):
        objective = objective.as_objective().get_coefficients()

    n_vars = len(objective)

    model = gb.Model()
    model.params.OutputFlag = int(verbose)

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

    _sense = {
        gb.GRB.MINIMIZE: gb.GRB.MINIMIZE,
        gb.GRB.MAXIMIZE: gb.GRB.MAXIMIZE,
        ilpy.Sense.Minimize: gb.GRB.MINIMIZE,
        ilpy.Sense.Maximize: gb.GRB.MAXIMIZE,
    }[sense]
    objective = sum(objective[i] * x[i] for i in range(n_vars))
    model.setObjective(objective, _sense)

    _op_map = {
        ilpy.Relation.GreaterEqual: operator.ge,
        ilpy.Relation.LessEqual: operator.le,
        ilpy.Relation.Equal: operator.eq,
        ">=": operator.ge,
        "<=": operator.le,
        "=": operator.eq,
    }

    for c in constraints:
        if isinstance(c, Expression):
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


@pytest.mark.skipif(not HAVE_GUROBI, reason="Gurobi not installed")
def test_non_convex_quadratic_gurobi() -> None:
    # currently, just a smoke test to make sure we don't crash on solve.
    obj = ilpy.Objective()
    obj.set_quadratic_coefficient(0, 0, -1)  # quadratic term (-x^2)

    solver = ilpy.Solver(
        1, ilpy.VariableType.Continuous, preference=ilpy.Preference.Gurobi
    )
    solver.set_objective(obj)

    constraint = ilpy.Constraint()
    constraint.set_coefficient(0, 1)
    constraint.set_value(1)
    solver.add_constraint(constraint)

    # Gurobi will raise an exception at the moment... may be changed later:
    with pytest.raises(RuntimeError, match="Q matrix is not positive semi-definite"):
        solver.solve()
