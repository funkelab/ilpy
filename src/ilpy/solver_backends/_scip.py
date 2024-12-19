from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ilpy._constants import Relation, Sense, SolverStatus, VariableType
from ilpy._solver import Solution

from ._base import SolverBackend

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ilpy._components import Constraint, Constraints, Objective

try:
    import pyscipopt as scip
    from pyscipopt import SCIP_EVENTTYPE
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

STATUS_MAP: Mapping[str, SolverStatus] = {
    "bestsollimit": SolverStatus.SOLUTIONLIMIT,
    "duallimit": SolverStatus.OTHER,
    "gaplimit": SolverStatus.SUBOPTIMAL,
    "infeasible": SolverStatus.INFEASIBLE,
    "inforunbd": SolverStatus.INF_OR_UNBOUNDED,
    "memlimit": SolverStatus.OTHER,
    "nodelimit": SolverStatus.NODELIMIT,
    "optimal": SolverStatus.OPTIMAL,
    "primallimit": SolverStatus.SUBOPTIMAL,
    "restartlimit": SolverStatus.OTHER,
    "sollimit": SolverStatus.SOLUTIONLIMIT,
    "stallnodelimit": SolverStatus.NODELIMIT,
    "timelimit": SolverStatus.TIMELIMIT,
    "totalnodelimit": SolverStatus.NODELIMIT,
    "unbounded": SolverStatus.UNBOUNDED,
    "unknown": SolverStatus.UNKNOWN,
    "userinterrupt": SolverStatus.USERINTERRUPT,
}
EVENT_NAME_MAP = {
    val: name for name, val in SCIP_EVENTTYPE.__dict__.items() if name.isupper()
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
        self._model.includeEventhdlr(
            EventHandler(self), "EventHandler", "Handles custom events"
        )

        # ilpy uses infinite bounds by default, but Gurobi uses 0 to infinity by default
        vtype = VTYPE_MAP[default_variable_type]
        self._vars: list[scip.Variable] = []
        for i in range(num_variables):
            self._vars.append(model.addVar(vtype=vtype, lb=-INF, name=f"x_{i}"))
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
        else:
            raise ValueError(f"Unsupported relation: {relation}")  # pragma: no cover

    def set_timeout(self, timeout: float) -> None:
        pass

    def set_optimality_gap(self, gap: float, absolute: bool) -> None:
        pass

    def set_num_threads(self, num_threads: int) -> None:
        pass

    def set_verbose(self, verbose: bool) -> None:
        pass

    def solve(self) -> Solution:
        self._model.optimize()  # TODO: event callback

        native_status = self._model.getStatus()
        status = STATUS_MAP.get(native_status, SolverStatus.OTHER)

        if not self._model.getNSols():
            variable_values = [0] * len(self._vars)
            objective_value = 0
        else:
            sol = self._model.getBestSol()
            variable_values = [self._model.getSolVal(sol, v) for v in self._vars]
            objective_value = self._model.getSolObjVal(sol)

        # Reset SCIP to allow adding constraints for future solves
        self._model.freeTransform()

        return Solution(
            variable_values=variable_values,
            objective_value=objective_value,
            status=status,
            time=self._model.getSolvingTime(),
            native_status=native_status,
        )

    def native_model(self) -> Any:
        return self._model


class EventHandler(scip.Eventhdlr):
    def __init__(self, backend: ScipSolver):
        """event handler to capture SCIP events and pass data to the backend."""
        self.backend = backend

    def eventinit(self) -> None:
        """Initialize the event handler and register the desired events."""
        # Register PRESOLVEROUND and BESTSOLFOUND events
        self.model.catchEvent(SCIP_EVENTTYPE.PRESOLVEROUND, self)
        self.model.catchEvent(SCIP_EVENTTYPE.BESTSOLFOUND, self)

    def eventexit(self) -> None:
        """Unregister events when the handler exits."""
        self.model.dropEvent(SCIP_EVENTTYPE.PRESOLVEROUND, self)
        self.model.dropEvent(SCIP_EVENTTYPE.BESTSOLFOUND, self)

    def eventexec(self, event: scip.Event) -> None:
        """Handle the event execution."""
        # Get the event type
        eventtype = event.getType()
        m = self.model
        event_type: str = EVENT_NAME_MAP.get(eventtype, "UNKNOWN")

        event_data = {
            "event_type": event_type,
            "backend": "scip",
            "deterministic_time": self.model.getSolvingTime(),
        }

        # Process PRESOLVEROUND event
        if eventtype == SCIP_EVENTTYPE.PRESOLVEROUND:
            event_data.update(
                {
                    "nativeconss": m.getNConss(),  # SCIPgetNConss
                    "nbinvars": m.getNBinVars(),  # SCIPgetNBinVars
                    "nintvars": m.getNIntVars(),  # SCIPgetNIntVars
                    "nimplvars": m.getNImplVars(),  # SCIPgetNImplVars
                    "nenabledconss": ...,  # SCIPgetNEnabledConss
                    "upperbound": ...,  # SCIPgetUpperbound
                    "nactiveconss": ...,  # SCIPgetNActiveConss
                    "cutoffbound": ...,  # SCIPgetCutoffbound
                    "nfixedvars": ...,  # SCIPgetNFixedVars
                }
            )

        # Process BESTSOLFOUND event
        elif eventtype == SCIP_EVENTTYPE.BESTSOLFOUND:
            event_data.update(
                {
                    "avgdualbound": ...,  # SCIPgetAvgDualbound
                    "avglowerbound": ...,  # SCIPgetAvgLowerbound
                    "dualbound": m.getDualbound(),  # SCIPgetDualbound
                    "gap": m.getGap(),  # SCIPgetGap
                    "lowerbound": ...,  # SCIPgetLowerbound
                    "nactiveconss": ...,  # SCIPgetNActiveConss
                    "nbestsolsfound": m.getNBestSolsFound(),  # SCIPgetNBestSolsFound
                    "nenabledconss": ...,  # SCIPgetNEnabledConss
                    "nlimsolsfound": m.getNLimSolsFound(),  # SCIPgetNLimSolsFound
                    "nlps": m.getNLPs(),  # SCIPgetNLPs
                    "nnzs": ...,  # SCIPgetNNZs
                    "nsolsfound": m.getNSolsFound(),  # SCIPgetNSolsFound
                    "primalbound": m.getPrimalbound(),  # SCIPgetPrimalbound
                    "transgap": ...,  # SCIPgetTransGap
                }
            )

        # Emit the processed event data
        self.backend.emit_event_data(event_data)  # type: ignore [arg-type]
