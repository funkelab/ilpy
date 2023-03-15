from ilpy.expressions import Index, _get_coefficients
import pytest

from ilpy.wrapper import Relation


@pytest.mark.parametrize(
    "expr_str, expected",
    [
        ("2 * u - 5 * v + e / 2 <= -3", {"u": 2, "v": -5, "e": 0.5, None: 3}),
        ("5 * (u - 3 * v) + 2 * e == 0", {"u": 5, "v": -15, "e": 2, None: 0}),
    ],
)
def test_expressions(expr_str, expected):
    # note that we're using letters here rather than numbers
    # for the sake of testing... but for an actual constraint
    # the Index instances want integers.
    ns = {"u": Index("u"), "v": Index("v"), "e": Index("e")}
    expr = eval(expr_str, ns)
    assert str(expr) == expr_str
    assert _get_coefficients(expr) == expected


def test_to_constraint():
    u = Index(0)
    v = Index(1)
    e = Index(2)

    expr = 2 * u - 5 * v + e / 2 <= -3
    constraint = expr.constraint()
    assert constraint.get_value() == -3
    assert constraint.get_relation() == Relation.LessEqual
    assert constraint.get_coefficients() == {0: 2.0, 1: -5.0, 2: 0.5}
