from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np

from ilpy._constants import Relation, Sense, SolverStatus, VariableType
from ilpy._solver import Solution

from ._base import SolverBackend

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ilpy._components import Constraint, Constraints, Objective
    from ilpy.event_data import GurobiData

try:
    import gurobipy as gb
    from gurobipy import GRB

except ImportError:
    raise ImportError(
        "gurobipy not installed, but required for GurobiSolver. "
        "please `pip install gurobipy` or `conda install -c gurobi gurobi`."
    ) from None

# map ilpy variable types to gurobipy variable types
VTYPE_MAP: Mapping[int, str] = {
    VariableType.Continuous: GRB.CONTINUOUS,
    VariableType.Binary: GRB.BINARY,
    VariableType.Integer: GRB.INTEGER,
}
SENSE_MAP: Mapping[Sense, int] = {
    Sense.Minimize: GRB.MINIMIZE,
    Sense.Maximize: GRB.MAXIMIZE,
}

STATUS_MAP: Mapping[int, SolverStatus] = {
    GRB.LOADED: SolverStatus.UNKNOWN,
    GRB.OPTIMAL: SolverStatus.OPTIMAL,
    GRB.INFEASIBLE: SolverStatus.INFEASIBLE,
    GRB.UNBOUNDED: SolverStatus.UNBOUNDED,
    GRB.INF_OR_UNBD: SolverStatus.INF_OR_UNBOUNDED,
    GRB.TIME_LIMIT: SolverStatus.TIMELIMIT,
    GRB.NODE_LIMIT: SolverStatus.NODELIMIT,
    GRB.SOLUTION_LIMIT: SolverStatus.SOLUTIONLIMIT,
    GRB.INTERRUPTED: SolverStatus.USERINTERRUPT,
    GRB.NUMERIC: SolverStatus.NUMERIC,
    GRB.SUBOPTIMAL: SolverStatus.SUBOPTIMAL,
}


class GurobiSolver(SolverBackend):
    def __init__(self) -> None:
        super().__init__()
        # we put this in __init__ instead of initialize so that it will raise an
        # exception inside of create_backend if the module is imported but the
        # license is not available
        self._model = gb.Model()
        # 2 = non-convex quadratic problems are solved by means of translating them
        # into bilinear form and applying spatial branching.
        self._model.params.NonConvex = 2

    def initialize(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: Mapping[int, VariableType],  # TODO
    ) -> None:
        self._reset()
        # clear if we have any
        # ilpy uses infinite bounds by default, but Gurobi uses 0 to infinity by default
        vtype = VTYPE_MAP[default_variable_type]
        self._vars = self._model.addVars(num_variables, lb=-GRB.INFINITY, vtype=vtype)

    def _reset(self) -> None:
        self._model.remove(self._model.getVars())
        self._model.remove(self._model.getConstrs())

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

    def _solver_callback(self, model: gb.Model, where: int) -> None:
        if data := _get_event_data(model, where):
            self.emit_event_data(data)

    def solve(self) -> Solution:
        self._model.optimize(self._solver_callback)

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


def get_event_type_name(where: int) -> str:
    event_names = {
        GRB.Callback.POLLING: "POLLING",
        GRB.Callback.PRESOLVE: "PRESOLVE",
        GRB.Callback.SIMPLEX: "SIMPLEX",
        GRB.Callback.MIP: "MIP",
        GRB.Callback.MIPSOL: "MIPSOL",
        GRB.Callback.MIPNODE: "MIPNODE",
        GRB.Callback.MESSAGE: "MESSAGE",
        GRB.Callback.BARRIER: "BARRIER",
        GRB.Callback.MULTIOBJ: "MULTIOBJ",
        GRB.Callback.IIS: "IIS",
    }
    return event_names.get(where, "UNKNOWN")


def _get_event_data(model: gb.Model, where: int) -> GurobiData | None:
    # POLLING callback: only called if no other callbacks have been triggered recently
    if where == GRB.Callback.POLLING:
        return None

    # Get the event type name
    event_name = get_event_type_name(where)

    # Initialize the event data dictionary
    event_data = {"event_type": event_name, "backend": "gurobi"}

    # Collect common callback data
    runtime = model.cbGet(GRB.Callback.RUNTIME)
    work = model.cbGet(GRB.Callback.WORK)
    event_data.update({"runtime": runtime, "work": work})

    if where == GRB.Callback.PRESOLVE:
        # Presolve-specific data
        event_data.update(
            {
                "pre_coldel": model.cbGet(GRB.Callback.PRE_COLDEL),
                "pre_rowdel": model.cbGet(GRB.Callback.PRE_ROWDEL),
                "pre_senchg": model.cbGet(GRB.Callback.PRE_SENCHG),
                "pre_bndchg": model.cbGet(GRB.Callback.PRE_BNDCHG),
                "pre_coechg": model.cbGet(GRB.Callback.PRE_COECHG),
            }
        )
    elif where == GRB.Callback.SIMPLEX:
        # Simplex-specific data
        event_data.update(
            {
                "itrcnt": model.cbGet(GRB.Callback.SPX_ITRCNT),
                "objval": model.cbGet(GRB.Callback.SPX_OBJVAL),
                "priminf": model.cbGet(GRB.Callback.SPX_PRIMINF),
                "dualinf": model.cbGet(GRB.Callback.SPX_DUALINF),
                "ispert": model.cbGet(GRB.Callback.SPX_ISPERT),
            }
        )
    elif where == GRB.Callback.MIP:
        # MIP-specific data
        objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
        objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
        event_data.update(
            {
                "objbst": objbst,
                "objbnd": objbnd,
                "nodcnt": model.cbGet(GRB.Callback.MIP_NODCNT),
                "solcnt": model.cbGet(GRB.Callback.MIP_SOLCNT),
                "cutcnt": model.cbGet(GRB.Callback.MIP_CUTCNT),
                "nodlft": model.cbGet(GRB.Callback.MIP_NODLFT),
                "itrcnt": model.cbGet(GRB.Callback.MIP_ITRCNT),
                "openscenarios": model.cbGet(GRB.Callback.MIP_OPENSCENARIOS),
                "phase": model.cbGet(GRB.Callback.MIP_PHASE),
                "primalbound": objbst,
                "dualbound": objbnd,
                "gap": 100
                * (abs(objbnd - objbst) / (np.finfo(float).eps + abs(objbst))),
            }
        )
    elif where == GRB.Callback.MIPSOL:
        # New MIP solution-specific data
        obj = model.cbGet(GRB.Callback.MIPSOL_OBJ)
        objbst = model.cbGet(GRB.Callback.MIPSOL_OBJBST)
        objbnd = model.cbGet(GRB.Callback.MIPSOL_OBJBND)
        event_data.update(
            {
                "obj": obj,
                "objbst": objbst,
                "objbnd": objbnd,
                "nodcnt": model.cbGet(GRB.Callback.MIPSOL_NODCNT),
                "solcnt": model.cbGet(GRB.Callback.MIPSOL_SOLCNT),
                "openscenarios": model.cbGet(GRB.Callback.MIPSOL_OPENSCENARIOS),
                "phase": model.cbGet(GRB.Callback.MIPSOL_PHASE),
                "primalbound": objbst,
                "dualbound": objbnd,
                "gap": 100
                * (abs(objbnd - objbst) / (np.finfo(float).eps + abs(objbst))),
            }
        )
    elif where == GRB.Callback.MESSAGE:
        # Message-specific data
        msg = model.cbGet(GRB.Callback.MSG_STRING)
        event_data["message"] = msg

    return cast("GurobiData", event_data)
