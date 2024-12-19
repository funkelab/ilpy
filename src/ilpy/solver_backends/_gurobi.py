from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ilpy._constants import Relation, Sense, SolverStatus, VariableType
from ilpy._solver import Solution

from ._base import SolverBackend

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ilpy._components import Constraint, Constraints, Objective

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
SENSE_MAP: Mapping[Sense, int] = {
    Sense.Minimize: gb.GRB.MINIMIZE,
    Sense.Maximize: gb.GRB.MAXIMIZE,
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
        variable_types: Mapping[int, VariableType],  # TODO
    ) -> None:
        self._model = model = gb.Model()
        # ilpy uses infinite bounds by default, but Gurobi uses 0 to infinity by default
        vtype = VTYPE_MAP[default_variable_type]
        self._vars = model.addVars(num_variables, lb=-gb.GRB.INFINITY, vtype=vtype)
        self._event_callback: Callable[[Mapping[str, float | str]], None] | None = None

        # 2 = non-convex quadratic problems are solved by means of translating them
        # into bilinear form and applying spatial branching.
        self._model.params.NonConvex = 2

    def set_objective(self, objective: Objective) -> None:
        obj: gb.LinExpr | gb.QuadExpr = gb.quicksum(
            coef * var for coef, var in zip(objective, self._vars.values())
        )
        for (i, j), qcoef in objective.get_quadratic_coefficients().items():
            obj += qcoef * self._vars[i] * self._vars[j]
        sense = SENSE_MAP[objective.get_sense()]
        self._model.setObjective(obj, sense)

    def set_constraints(self, constraints: Constraints) -> None:
        # clear existing constraints
        self._model.remove(self._model.getConstrs())

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
        else:
            raise ValueError(f"Unsupported relation: {relation}")  # pragma: no cover

    def set_timeout(self, timeout: float) -> None:
        self._model.params.TimeLimit = timeout

    def set_optimality_gap(self, gap: float, absolute: bool) -> None:
        if absolute:
            self._model.params.MIPGapAbs = gap
        else:
            self._model.params.MIPGap = gap

    def set_num_threads(self, num_threads: int) -> None:
        self._model.params.Threads = num_threads

    def set_verbose(self, verbose: bool) -> None:
        self._model.params.OutputFlag = 1 if verbose else 0

    def set_event_callback(
        self, callback: Callable[[Mapping[str, float | str]], None] | None
    ) -> None:
        self._event_callback = callback

    def solve(self) -> Solution:
        self._model.optimize()  # TODO: event callback

        native_status = self._model.Status
        status = STATUS_MAP.get(native_status, SolverStatus.OTHER)

        solcount = self._model.SolCount
        if (
            status
            in (SolverStatus.OPTIMAL, SolverStatus.SUBOPTIMAL, SolverStatus.TIMELIMIT)
            and solcount > 0
        ):
            solution = [var.X for var in self._vars.values()]
            objective_value = self._model.ObjVal
        elif status == SolverStatus.TIMELIMIT:
            solution = [var.X for var in self._vars.values()]
            objective_value = self._model.ObjVal
        else:
            solution = [0] * len(self._vars)
            objective_value = 0

        return Solution(
            variable_values=solution,
            objective_value=objective_value,
            time=self._model.Runtime,
            status=status,
            native_status=native_status,
        )

    def native_model(self) -> gb.Model:
        return self._model
