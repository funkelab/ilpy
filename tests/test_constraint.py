import ilpy


def test_constraint() -> None:
    constraint = ilpy.Constraint()
    constraint.set_coefficient(0, 1)
    constraint.set_quadratic_coefficient(1, 1, 1)


def test_is_violated() -> None:
    x = ilpy.Variable("x", index=0)
    solution = ilpy.Solution([0.1 + 0.2], 0, ilpy.SolverStatus.OPTIMAL, 0)
    assert not (x == 0.3).as_constraint().is_violated(solution)
    solution = ilpy.Solution([2.0], 0, ilpy.SolverStatus.OPTIMAL, 0)
    assert (x * x <= 1).as_constraint().is_violated(solution)
