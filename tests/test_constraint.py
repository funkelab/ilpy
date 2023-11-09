import ilpy


def test_constraint() -> None:
    constraint = ilpy.Constraint()
    constraint.set_coefficient(0, 1)
    constraint.set_quadratic_coefficient(1, 1, 1)
