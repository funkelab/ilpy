import ilpy


def test_resize() -> None:
    obj = ilpy.Objective()
    assert len(obj) == 0

    obj.set_coefficient(0, 2)  # linear term (2x)
    assert len(obj) == 1

    obj.set_quadratic_coefficient(1, 1, 3)  # quadratic term (3y^2)
    assert len(obj) == 2

    obj2 = ilpy.Objective()
    obj2.set_quadratic_coefficient(0, 0, 1)  # quadratic term (x^2)
    assert len(obj2) == 1
