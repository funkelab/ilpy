from ilpy.expressions import Index, _get_coefficients
import pytest


@pytest.mark.parametrize(
    "expr_str, expected",
    [
        ("2 * u - 5 * v + e / 2 <= -3", {"u": 2, "v": -5, "e": 0.5, None: 3}),
        ("5 * (u - 3 * v) + 2 * e == 0", {"u": 5, "v": -15, "e": 2, None: 0}),
    ],
)
def test_expressions(expr_str, expected):
    ns = {"u": Index("u"), "v": Index("v"), "e": Index("e")}
    expr = eval(expr_str, ns)
    assert str(expr) == expr_str
    assert _get_coefficients(expr) == expected
