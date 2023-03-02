import ilpy
import unittest
import logging

logging.basicConfig(level=logging.INFO)


class TestSolvers(unittest.TestCase):

    def simple_solver_test(self, preference):

        num_vars = 10
        special_var = 5

        solver = ilpy.LinearSolver(
            num_vars,
            ilpy.VariableType.Binary,
            {
                special_var: ilpy.VariableType.Continuous
            },
            preference)

        objective = ilpy.LinearObjective()
        for i in range(num_vars):
            objective.set_coefficient(i, 1.0)
        objective.set_coefficient(special_var, 0.5)

        constraint = ilpy.LinearConstraint()
        for i in range(num_vars):
            constraint.set_coefficient(i, 1.0)
        constraint.set_relation(ilpy.Relation.Equal)
        constraint.set_value(1.0)

        solver.set_objective(objective)
        solver.add_constraint(constraint)

        solution, msg = solver.solve()

        self.assertEqual(solution[5], 1)

    def test_any(self):
        self.simple_solver_test(ilpy.Preference.Any)

    def test_gurobi(self):
        self.simple_solver_test(ilpy.Preference.Gurobi)


# XFAIL gurobi if not installed
# this is the best way I could find to determine this so far
try:
    ilpy.LinearSolver(0, ilpy.VariableType.Binary, None, ilpy.Preference.Gurobi)
except RuntimeError:
    unittest.expectedFailure(TestSolvers.test_gurobi)
