from collections.abc import Mapping
from typing import Callable

from ilpy._components import Constraint, Constraints, Objective
from ilpy._constants import Relation, Sense, SolverStatus, VariableType
from ilpy._solver import Solution

from ._base import SolverBackend

try:
    import gurobipy as gb
except ImportError:
    raise ImportError(
        "Gurobipy not installed, but required for GurobiSolver. "
        "please `conda install -c gurobi gurobi"
    ) from None

# map ilpy variable types to gurobipy variable types
VTYPE_MAP: Mapping[int, str] = {
    VariableType.Continuous: gb.GRB.CONTINUOUS,
    VariableType.Binary: gb.GRB.BINARY,
    VariableType.Integer: gb.GRB.INTEGER,
}

STATUS_MAP: Mapping[int, SolverStatus] = {
    gb.GRB.LOADED: SolverStatus.UNKNOWN,
    gb.GRB.OPTIMAL: SolverStatus.OPTIMAL,
    gb.GRB.INFEASIBLE: SolverStatus.INFEASIBLE,
    gb.GRB.UNBOUNDED: SolverStatus.UNBOUNDED,
    gb.GRB.INF_OR_UNBD: SolverStatus.INF_OR_UNBOUNDED,
    gb.GRB.TIME_LIMIT: SolverStatus.TIMELIMIT,
    gb.GRB.NODE_LIMIT: SolverStatus.NODELIMIT,
    gb.GRB.SOLUTION_LIMIT: SolverStatus.SOLUTIONLIMIT,
    gb.GRB.INTERRUPTED: SolverStatus.USERINTERRUPT,
    gb.GRB.NUMERIC: SolverStatus.NUMERIC,
    gb.GRB.SUBOPTIMAL: SolverStatus.SUBOPTIMAL,
}


class GurobiSolver(SolverBackend):
    def initialize(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: Mapping[int, VariableType],
    ) -> None:
        self._model = model = gb.Model()
        # ilpy uses infinite bounds by default, but Gurobi uses 0 to infinity by default
        vtype = VTYPE_MAP[default_variable_type]
        self._vars = model.addVars(num_variables, lb=-gb.GRB.INFINITY, vtype=vtype)
        self._event_callback: Callable[[Mapping[str, float | str]], None] | None = None

    def set_objective(self, objective: Objective) -> None:
        sense = (
            gb.GRB.MINIMIZE
            if objective.get_sense() == Sense.Minimize
            else gb.GRB.MAXIMIZE
        )
        obj: gb.LinExpr | gb.QuadExpr = gb.quicksum(
            coef * var for coef, var in zip(objective, self._vars)
        )
        for (i, j), qcoef in objective.get_quadratic_coefficients().items():
            obj += qcoef * self._vars[i] * self._vars[j]
        self._model.setObjective(obj, sense)

    def set_constraints(self, constraints: Constraints) -> None:
        for constraint in constraints:
            self.add_constraint(constraint)

    def add_constraint(self, constraint: Constraint) -> None:
        coefs = constraint.get_coefficients()
        qcoefs = constraint.get_quadratic_coefficients()
        relation = constraint.get_relation()
        value = constraint.get_value()
        left: gb.QuadExpr | gb.LinExpr = gb.quicksum(
            lcoef * self._vars[idx] for idx, lcoef in coefs.items()
        )
        for (i, j), qcoef in qcoefs.items():
            left = left + qcoef * self._vars[i] * self._vars[j]
        if relation == Relation.LessEqual:
            self._model.addConstr(left <= value)
        elif relation == Relation.GreaterEqual:
            self._model.addConstr(left >= value)
        elif relation == Relation.Equal:
            self._model.addConstr(left == value)

    def set_timeout(self, timeout: float) -> None:
        self._model.params.TimeLimit = timeout

    def set_optimality_gap(self, gap: float, absolute: bool) -> None:
        self._model.params.MIPGap = gap
        self._model.params.MIPGapAbs = int(absolute)

    def set_num_threads(self, num_threads: int) -> None:
        self._model.params.Threads = num_threads

    def set_verbose(self, verbose: bool) -> None:
        self._model.params.OutputFlag = int(verbose)

    def set_event_callback(
        self, callback: Callable[[Mapping[str, float | str]], None] | None
    ) -> None:
        self._event_callback = callback

    def solve(self) -> Solution:
        self._model.optimize()  # TODO: event callback

        status = STATUS_MAP.get(self._model.Status, SolverStatus.OTHER)

        if status == SolverStatus.OPTIMAL:
            solution = [var.X for var in self._vars.values()]
        else:
            solution = [0] * len(self._vars)

        return Solution(solution, self._model.ObjVal, status, time=self._model.Runtime)
