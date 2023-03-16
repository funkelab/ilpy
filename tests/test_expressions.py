from ilpy.expressions import Expression, Variable, _get_coefficients
import pytest

from ilpy.wrapper import Relation
import operator

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
    u = Variable("u", index=0)
    v = Variable("v", index=1)
    e = Variable("e", index=2)

    expr = 2 * u - 5 * v + e / 2 >= -3
    constraint = expr.constraint()
    assert constraint.get_value() == -3
    assert constraint.get_relation() == Relation.GreaterEqual
    assert constraint.get_coefficients() == {0: 2.0, 1: -5.0, 2: 0.5}


def test_expression_errors():
    # constant terms must be numeric
    assert isinstance(Variable("u") + 1, Expression)
    assert isinstance(Variable("u") + 3.14, Expression)
    with pytest.raises(TypeError, match="Constants must be numbers"):
        Variable("u") + "not a number"

    # linear constraints may not multiply variables by each other
    with pytest.raises(ValueError, match="Multiplication must be by a constant"):
        (Variable("u", index=0) * Variable("v", index=1)).constraint()

    # linear constraints may not multiply variables by each other
    with pytest.raises(ValueError, match="Unsupported comparison"):
        (Variable("v", index=0) != 1).constraint()

    # cannot cast to a constraint without a variable index
    with pytest.raises(
        ValueError, match="All variables in a constraint expression must have an index"
    ):
        (Variable("u") <= 0).constraint()
