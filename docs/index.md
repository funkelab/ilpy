# Welcome to ilpy's documentation

**ilpy** is a Python library that provides unified wrappers for popular Integer
Linear Programming (ILP) solvers such as Gurobi and SCIP. It offers a
consistent API that abstracts away the differences between solver
implementations.

With ilpy, you can:

- Define linear and quadratic optimization problems using a simple, intuitive syntax
- Express constraints using natural Python expressions
- Switch between different solver backends (currently Gurobi and SCIP)
- Monitor solver progress through callback events
- Support for continuous, binary, and integer variables

## Quick start

Solve a small linear program — minimize `2x + 3y` subject to `3x + 2y >= 10`
and `x + 2y >= 8`:

===+ "Functional API"

    Express the problem using natural Python expressions:

    ```python
    import ilpy
    from ilpy.expressions import Variable

    x = Variable("x", index=0)
    y = Variable("y", index=1)

    solution = ilpy.solve(
        objective=2 * x + 3 * y,
        constraints=[3 * x + 2 * y >= 10, x + 2 * y >= 8],
    )
    print(list(solution))       # [1.0, 3.5]
    print(solution.get_value()) # 12.5
    ```

    Or pass raw coefficients directly:

    ```python
    import ilpy

    solution = ilpy.solve(
        objective=[2, 3],
        constraints=[
            ([3, 2], ">=", 10),
            ([1, 2], ">=", 8),
        ],
    )
    ```

=== "Object-oriented API"

    Build the problem from `Expression` objects, then hand it to a `Solver`:

    ```python
    import ilpy
    from ilpy.expressions import Variable

    x = Variable("x", index=0)
    y = Variable("y", index=1)

    solver = ilpy.Solver(2, ilpy.Continuous)
    solver.set_objective(2 * x + 3 * y)
    solver.add_constraint(3 * x + 2 * y >= 10)
    solver.add_constraint(x + 2 * y >= 8)

    solution = solver.solve()
    print(list(solution))       # [1.0, 3.5]
    print(solution.get_value()) # 12.5
    ```

    Or assemble `Objective` and `Constraint` objects imperatively:

    ```python
    import ilpy

    objective = ilpy.Objective()
    objective.set_coefficient(0, 2)
    objective.set_coefficient(1, 3)

    c1 = ilpy.Constraint()
    c1.set_coefficient(0, 3)
    c1.set_coefficient(1, 2)
    c1.set_relation(ilpy.GreaterEqual)
    c1.set_value(10)

    c2 = ilpy.Constraint()
    c2.set_coefficient(0, 1)
    c2.set_coefficient(1, 2)
    c2.set_relation(ilpy.GreaterEqual)
    c2.set_value(8)

    solver = ilpy.Solver(2, ilpy.Continuous)
    solver.set_objective(objective)
    solver.add_constraint(c1)
    solver.add_constraint(c2)

    solution = solver.solve()
    ```

## Contents

- [API Reference](api.md)
