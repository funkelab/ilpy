import operator
import os
import sys

import pytest

from ilpy import (
    Constraint,
    Constraints,
    Objective,
    Relation,
    Sense,
    Solver,
    VariableType,
)
from ilpy.expressions import Expression, Variable, _get_coefficients

u = Variable("u")
v = Variable("v")
e = Variable("e")
ns = {"u": u, "v": v, "e": e}


@pytest.mark.parametrize(
    "expr_str, expected",
    [
        ("2 * u - 5 * v + e / 2 <= -3", {u: 2, v: -5, e: 0.5, None: 3}),
        ("5 * (u - 3 * v) + 2 * e == 0", {u: 5, v: -15, e: 2, None: 0}),
        ("(u - 3) * 2 >= e + 5", {u: 2, e: -1, None: -11}),
        ("+u == -v - 2", {u: 1, v: 1, None: 2}),
    ],
)
def test_expressions(expr_str, expected):
    expr = eval(expr_str, ns)
    # Note: this string assertion precludes the future possibility of immediately
    # simplify expressions as they are created... so we may want to remove it.
    # (or test it independently with already-simplified expressions)
    assert str(expr) == expr_str
    assert _get_coefficients(expr) == expected


@pytest.mark.parametrize("compop", ["le", "lt", "ge", "gt", "eq", "ne"])
def test_comparisons(compop: str):
    """smoke test for all comparison types."""
    compare = getattr(operator, compop)
    compare(Variable("u"), 1)
    compare(1, Variable("u"))


@pytest.mark.parametrize("binop", ["add", "sub", "mul", "truediv"])
def test_binops(binop: str):
    """smoke test for all binary operations."""
    operate = getattr(operator, binop)
    operate(Variable("u"), 1)
    operate(1, Variable("u"))


def test_to_constraint():
    """Test a couple of expressions that can be converted to constraints."""
    u = Variable("u", index=0)
    v = Variable("v", index=1)
    e = Variable("e", index=2)

    expr = 2 * u - 5 * v + e / 2 >= -3
    constraint = expr.as_constraint()
    assert isinstance(constraint, Constraint)
    assert constraint.get_value() == -3
    assert constraint.get_relation() == Relation.GreaterEqual
    assert constraint.get_coefficients() == {0: 2.0, 1: -5.0, 2: 0.5}

    expr = u == v
    constraint = expr.as_constraint()
    assert isinstance(constraint, Constraint)
    assert constraint.get_value() == 0
    assert constraint.get_relation() == Relation.Equal
    assert constraint.get_coefficients() == {0: 1.0, 1: -1.0}


def test_to_objective() -> None:
    """Test a couple of expressions that can be converted to objective."""
    u = Variable("u", index=0)
    v = Variable("v", index=1)
    e = Variable("e", index=3)

    expr: Expression = u - 2 * v + 3
    constraint = expr.as_objective(Sense.Maximize)
    assert isinstance(constraint, Objective)
    assert constraint.get_constant() == 3
    assert constraint.get_sense() == Sense.Maximize
    assert constraint.get_coefficients() == [1.0, -2.0]

    expr = 4 * e - 2 * u
    constraint = expr.as_objective()
    assert isinstance(constraint, Objective)
    assert constraint.get_constant() == 0
    assert constraint.get_sense() == Sense.Minimize
    assert constraint.get_coefficients() == [-2.0, 0, 0, 4]

    expr = -2 * u**2 - 3 * v * e + 4 * v + 5
    constraint = expr.as_objective()
    assert isinstance(constraint, Objective)
    assert constraint.get_constant() == 5
    assert constraint.get_sense() == Sense.Minimize
    assert constraint.get_quadratic_coefficients() == {
        (u.index, u.index): -2,
        (v.index, e.index): -3.0,
    }
    assert constraint.get_coefficients()[v.index] == 4

    expr = u * (v - 2 * 6 * e)
    constraint = expr.as_objective()
    assert isinstance(constraint, Objective)
    assert constraint.get_constant() == 0
    assert constraint.get_sense() == Sense.Minimize
    assert constraint.get_quadratic_coefficients() == {
        (u.index, v.index): 1,
        (u.index, e.index): -12,
    }


def test_sum() -> None:
    """Check that sum works (mimics some of the expressions in motile)"""
    n = 10
    expr1 = (
        n * Variable("a", 0) - sum(Variable(str(x), x) for x in range(1, 4))
    ) <= n - 1
    constraint1 = expr1.as_constraint()
    assert constraint1.get_value() == 9
    assert constraint1.get_relation() == Relation.LessEqual
    assert constraint1.get_coefficients() == {0: 10.0, 1: -1.0, 2: -1.0, 3: -1.0}


def test_expression_errors():
    # constant terms must be numeric
    assert isinstance(Variable("u") + 1, Expression)
    assert isinstance(Variable("u") + 3.14, Expression)
    with pytest.raises(TypeError, match="Constants must be numbers"):
        Variable("u") + "not a number"

    # linear constraints may not multiply variables by each other
    with pytest.raises(ValueError, match="Unsupported comparison"):
        (Variable("v", index=0) != 1).as_constraint()

    # linear constraints may not multiply variables by each other
    with pytest.raises(TypeError, match="Cannot multiply by more than two"):
        e = Variable("u", index=0) * Variable("v", index=1) * Variable("x", index=2)
        e.as_objective()

    # cannot cast to a constraint without a variable index
    with pytest.raises(
        ValueError, match="All variables in an Expression must have an index"
    ):
        (Variable("u") <= 0).as_constraint()


def test_adding() -> None:
    """Test various add() overloads accept expressions as well as objects."""

    u = Variable("u", index=0)
    constraints = Constraints()
    constraints.add(u >= 10)

    solver = Solver(2, VariableType.Integer)
    solver.set_objective(u)
    solver.add_constraint(u >= 0)
    solver.set_constraints(constraints)


@pytest.mark.skipif(
    sys.version_info < (3, 11) and os.name == "nt",
    reason="fails too often on windows 3.10",
)
def test_recursion() -> None:
    from ilpy.expressions import recursion_limit_raised_by

    reclimit = sys.getrecursionlimit()
    s = sum(Variable(str(x), index=x) for x in range(reclimit + 5001))
    SOME_MAX = 1000
    expr = s <= SOME_MAX
    with pytest.raises(RecursionError):
        expr.as_constraint()
    with recursion_limit_raised_by():
        assert isinstance(expr.as_constraint(), Constraint)
