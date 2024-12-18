from collections.abc import Mapping
from typing import Any, Callable, Literal

from ilpy._components import Constraint, Constraints, Objective
from ilpy._constants import Relation, Sense, SolverStatus, VariableType
from ilpy._solver import Solution

from ._base import SolverBackend

try:
    import pyscipopt as scip
except ImportError:
    raise ImportError(
        "pyscipopt not installed, but required for GurobiSolver. "
        "please `pip install pyscipopt`"
    ) from None

# map ilpy variable types to gurobipy variable types
VTYPE_MAP: Mapping[int, str] = {
    VariableType.Continuous: "C",
    VariableType.Binary: "B",
    VariableType.Integer: "I",
}
STATUS_MAP: Mapping[int, SolverStatus] = {
    scip.SCIP_STATUS.UNKNOWN: SolverStatus.UNKNOWN,
    scip.SCIP_STATUS.OPTIMAL: SolverStatus.OPTIMAL,
    scip.SCIP_STATUS.INFEASIBLE: SolverStatus.INFEASIBLE,
    scip.SCIP_STATUS.UNBOUNDED: SolverStatus.UNBOUNDED,
    scip.SCIP_STATUS.INFORUNBD: SolverStatus.INF_OR_UNBOUNDED,
    scip.SCIP_STATUS.TIMELIMIT: SolverStatus.TIMELIMIT,
    scip.SCIP_STATUS.NODELIMIT: SolverStatus.NODELIMIT,
    scip.SCIP_STATUS.SOLLIMIT: SolverStatus.SOLUTIONLIMIT,
    scip.SCIP_STATUS.USERINTERRUPT: SolverStatus.USERINTERRUPT,
    scip.SCIP_STATUS.NUMERIC: SolverStatus.NUMERIC,
    scip.SCIP_STATUS.SUBOPTIMAL: SolverStatus.SUBOPTIMAL,
}

INF = float("inf")


class ScipSolver(SolverBackend):
    def initialize(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: Mapping[int, VariableType],
    ) -> None:
        self._model = model = scip.Model()
        # ilpy uses infinite bounds by default, but Gurobi uses 0 to infinity by default
        vtype = VTYPE_MAP[default_variable_type]
        self._vars = []
        for i in range(num_variables):
            self._vars.append(model.addVar(vtype=vtype, lb=-INF, name=f"x_{i}"))
        self._event_callback: Callable[[Mapping[str, float | str]], None] | None = None
        self.use_epigraph_reformulation = False

    def set_objective(
        self, objective: Objective, *, use_epigraph: bool | None = None
    ) -> None:
        # Create linear part of the objective
        obj = scip.quicksum(coef * var for coef, var in zip(objective, self._vars))
        obj = obj + objective.get_constant()
        sense = "minimize" if objective.get_sense() == Sense.Minimize else "maximize"

        # Add quadratic terms using auxiliary variables
        if quad_coeffs := objective.get_quadratic_coefficients():
            if use_epigraph is None:
                use_epigraph = self.use_epigraph_reformulation
            if use_epigraph:
                for (i, j), qcoef in quad_coeffs.items():
                    obj += qcoef * self._vars[i] * self._vars[j]
                self._set_nonlinear_objective(obj, sense)  # type: ignore [arg-type]
                return
            else:
                self._add_quad_auxiliary_variables(quad_coeffs)

        self._model.setObjective(obj, sense=sense)

    def _set_nonlinear_objective(
        self, expr: Any, sense: Literal["minimize", "maximize"]
    ) -> None:
        """Handles epigraph reformulation for nonlinear objectives."""
        new_obj = self._model.addVar(lb=-INF, obj=1)  # Surrogate objective variable
        if sense == "minimize":
            self._model.addCons(expr <= new_obj)
            self._model.setMinimize()
        elif sense == "maximize":
            self._model.addCons(expr >= new_obj)
            self._model.setMaximize()

    def _add_quad_auxiliary_variables(
        self, quad_coeffs: Mapping[tuple[int, int], float]
    ) -> None:
        for (i, j), value in quad_coeffs.items():
            if value != 0:
                # create z_ij and add val * z_ij to objective
                # z_ij cand be unbounded and real, it inherits all other
                # bounds/integrality from the x_i * x_j = z_ij constraint below
                z_ij = self._model.addVar(
                    name=f"z_{i},{j}", lb=-INF, ub=INF, obj=value, vtype="C"
                )
                # add the constraint x_i * x_j - z_ij = 0
                self._model.addCons(self._vars[i] * self._vars[j] - z_ij == 0)

    def set_constraints(self, constraints: Constraints) -> None:
        for constraint in constraints:
            self.add_constraint(constraint)

    def add_constraint(self, constraint: Constraint) -> None:
        coefs = constraint.get_coefficients()
        qcoefs = constraint.get_quadratic_coefficients()
        relation = constraint.get_relation()
        value = constraint.get_value()
        left = scip.quicksum(lcoef * self._vars[idx] for idx, lcoef in coefs.items())
        for (i, j), qcoef in qcoefs.items():
            left = left + qcoef * self._vars[i] * self._vars[j]
        if relation == Relation.LessEqual:
            self._model.addCons(left <= value)
        elif relation == Relation.GreaterEqual:
            self._model.addCons(left >= value)
        elif relation == Relation.Equal:
            self._model.addCons(left == value)

    def set_timeout(self, timeout: float) -> None:
        pass

    def set_optimality_gap(self, gap: float, absolute: bool) -> None:
        pass

    def set_num_threads(self, num_threads: int) -> None:
        pass

    def set_verbose(self, verbose: bool) -> None:
        pass

    def set_event_callback(
        self, callback: Callable[[Mapping[str, float | str]], None] | None
    ) -> None:
        self._event_callback = callback

    def solve(self) -> Solution:
        self._model.optimize()  # TODO: event callback

        status = STATUS_MAP.get(self._model.getStatus(), SolverStatus.OTHER)

        return Solution(
            [self._model.getVal(var) for var in self._vars],
            self._model.getObjVal(),
            status,
            time=self._model.getSolvingTime(),
        )
