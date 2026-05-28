"""NVIDIA cuOpt backend for ilpy.

cuOpt is an Apache-2.0 GPU MIP/LP solver
(https://docs.nvidia.com/cuopt/), distributed as the ``cuopt-cu12`` wheel on
``pypi.nvidia.com``. It accepts a sparse problem definition (CSR constraint
matrix + objective vector + row/column bounds + variable types) and solves
on a single CUDA device.

This backend buffers the ilpy ``Objective`` / ``Constraints`` set on it via
the standard ``SolverBackend`` API, then at ``solve()`` time materialises a
``cuopt.linear_programming.DataModel`` and dispatches a synchronous solve.

Quality validation context: on a 10.3 M-variable / 5.5 M-constraint cell-
tracking ILP, cuOpt returned an Optimal solution (relative gap < 1e-5) whose
selected-variable set matched a Gurobi-completed reference within rounding
error (<0.01 % of variables differ). See the upstream consumer
(eet_inference / hoct_inference) for the validation harness.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from ilpy._constants import Relation, Sense, SolverStatus, VariableType
from ilpy._solver import Solution

from ._base import SolverBackend

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ilpy._components import Constraint, Constraints, Objective

try:
    import numpy as np
    from cuopt.linear_programming import data_model, solver
    from cuopt.linear_programming.internals import GetSolutionCallback
    from cuopt.linear_programming.solver_settings import SolverSettings
    from scipy.sparse import csr_matrix
except ImportError as e:
    raise ImportError(
        "cuopt-cu12 (and numpy/scipy) are required for CuOptSolver. "
        "Install with:\n"
        "    pip install --extra-index-url https://pypi.nvidia.com cuopt-cu12"
    ) from e


# ilpy.VariableType → cuOpt single-char variable kind code
VTYPE_MAP: Mapping[int, bytes] = {
    VariableType.Continuous: b"C",
    VariableType.Binary: b"I",  # cuOpt uses {0,1} bounds + integer to model binary
    VariableType.Integer: b"I",
}

# cuOpt termination_status enum values (from cuopt.linear_programming):
#   1 = Optimal, 2 = Infeasible, 3 = Unbounded, 4 = TimeLimit, 5 = IterationLimit,
#   6 = Numerical, 7 = PrimalFeasible (heuristic-only, no dual bound)
STATUS_MAP: Mapping[int, SolverStatus] = {
    1: SolverStatus.OPTIMAL,
    2: SolverStatus.INFEASIBLE,
    3: SolverStatus.UNBOUNDED,
    4: SolverStatus.TIMELIMIT,
    5: SolverStatus.NODELIMIT,
    6: SolverStatus.OTHER,
    7: SolverStatus.SUBOPTIMAL,
}

INF = float("inf")


class CuOptSolver(SolverBackend):
    """ilpy SolverBackend implementation backed by NVIDIA cuOpt (GPU).

    Buffers variables, objective, constraints, and parameters until
    ``solve()`` is called, then materialises a cuOpt ``DataModel`` /
    ``SolverSettings`` pair and dispatches a synchronous GPU solve.
    """

    def __init__(self) -> None:
        super().__init__()
        # Buffered model state
        self._num_variables: int = 0
        self._var_types: np.ndarray | None = None  # array of bytes ("C"/"I")
        self._var_lb: np.ndarray | None = None
        self._var_ub: np.ndarray | None = None
        self._objective: Objective | None = None
        self._sense: Sense = Sense.Minimize
        self._constraint_buf: list[Constraint] = []
        # Solver parameters
        self._time_limit: float | None = None
        self._mip_gap_rel: float | None = None
        self._mip_gap_abs: float | None = None
        self._num_threads: int | None = None
        self._verbose: bool = False
        # The last assembled DataModel (for `native_model()`)
        self._last_dm: Any = None

    # ------------------------------------------------------------------ setup

    def initialize(
        self,
        num_variables: int,
        default_variable_type: VariableType,
        variable_types: Mapping[int, VariableType],
    ) -> None:
        self._num_variables = int(num_variables)
        self._var_types = np.array(
            [
                VTYPE_MAP[variable_types.get(i, default_variable_type)]
                for i in range(num_variables)
            ],
            dtype=object,
        )
        lb = np.empty(num_variables, dtype=np.float64)
        ub = np.empty(num_variables, dtype=np.float64)
        for i in range(num_variables):
            vt = variable_types.get(i, default_variable_type)
            if vt == VariableType.Binary:
                lb[i] = 0.0
                ub[i] = 1.0
            else:
                lb[i] = -INF
                ub[i] = INF
        self._var_lb = lb
        self._var_ub = ub
        # Reset constraint buffer (initialize is the start of a fresh model)
        self._constraint_buf = []

    # ------------------------------------------------------------ objective

    def set_objective(self, objective: Objective) -> None:
        if objective.get_quadratic_coefficients():
            raise NotImplementedError(
                "CuOptSolver does not currently support quadratic objectives. "
                "Use the SCIP or Gurobi backend for QP/MIQP problems."
            )
        self._objective = objective
        self._sense = objective.get_sense()

    # ----------------------------------------------------------- constraints

    def set_constraints(self, constraints: Constraints) -> None:
        self._constraint_buf = list(constraints)

    def add_constraint(self, constraint: Constraint) -> None:
        if constraint.get_quadratic_coefficients():
            raise NotImplementedError(
                "CuOptSolver does not currently support quadratic constraints. "
                "Use the SCIP or Gurobi backend for QCP/MIQCP problems."
            )
        self._constraint_buf.append(constraint)

    # ------------------------------------------------------------ parameters

    def set_timeout(self, timeout: float) -> None:
        self._time_limit = float(timeout)

    def set_optimality_gap(self, gap: float, absolute: bool) -> None:
        if absolute:
            self._mip_gap_abs = float(gap)
        else:
            self._mip_gap_rel = float(gap)

    def set_num_threads(self, num_threads: int) -> None:
        # cuOpt is GPU-bound; threads has no host-side effect. Recorded for
        # introspection but not forwarded.
        self._num_threads = int(num_threads)

    def set_verbose(self, verbose: bool) -> None:
        self._verbose = bool(verbose)

    # ----------------------------------------------------------------- solve

    def solve(self) -> Solution:
        if self._num_variables == 0:
            raise ValueError("CuOptSolver: initialize() must be called before solve().")
        if self._objective is None:
            raise ValueError(
                "CuOptSolver: set_objective() must be called before solve()."
            )

        import time as _time

        n_vars = self._num_variables
        n_cons = len(self._constraint_buf)

        # Objective vector
        obj_coefs = np.zeros(n_vars, dtype=np.float64)
        raw = self._objective.get_coefficients()
        if hasattr(raw, "items"):
            for vi, c in raw.items():
                obj_coefs[vi] = c
        else:
            # Sequence form: index → coefficient by position
            for vi, c in enumerate(list(raw)):
                obj_coefs[vi] = c
        # ilpy may report a constant on the objective; cuOpt has no
        # objective-constant parameter, so we capture it and add it to the
        # objective value we return.
        obj_constant = float(self._objective.get_constant())

        # Constraint matrix (CSR) + row bounds
        if n_cons > 0:
            rows: list[int] = []
            cols: list[int] = []
            vals: list[float] = []
            rels = np.empty(n_cons, dtype=np.int32)
            rhs = np.empty(n_cons, dtype=np.float64)
            for ri, c in enumerate(self._constraint_buf):
                for vi, v in c.get_coefficients().items():
                    rows.append(ri)
                    cols.append(vi)
                    vals.append(v)
                rels[ri] = int(c.get_relation())
                rhs[ri] = c.get_value()
            A = csr_matrix(
                (
                    np.asarray(vals, dtype=np.float64),
                    (
                        np.asarray(rows, dtype=np.int64),
                        np.asarray(cols, dtype=np.int64),
                    ),
                ),
                shape=(n_cons, n_vars),
            )
            row_lb = np.empty(n_cons, dtype=np.float64)
            row_ub = np.empty(n_cons, dtype=np.float64)
            le = rels == int(Relation.LessEqual)
            eq = rels == int(Relation.Equal)
            ge = rels == int(Relation.GreaterEqual)
            row_lb[le] = -INF
            row_ub[le] = rhs[le]
            row_lb[eq] = rhs[eq]
            row_ub[eq] = rhs[eq]
            row_lb[ge] = rhs[ge]
            row_ub[ge] = INF
        else:
            # Empty constraint set: build a 0-by-n_vars matrix to keep cuOpt happy.
            A = csr_matrix((n_cons, n_vars), dtype=np.float64)
            row_lb = np.zeros(0, dtype=np.float64)
            row_ub = np.zeros(0, dtype=np.float64)

        # Assemble DataModel
        dm = data_model.DataModel()
        dm.set_csr_constraint_matrix(A.data, A.indices, A.indptr)
        dm.set_constraint_lower_bounds(row_lb)
        dm.set_constraint_upper_bounds(row_ub)
        dm.set_objective_coefficients(obj_coefs)
        dm.set_variable_lower_bounds(self._var_lb)
        dm.set_variable_upper_bounds(self._var_ub)
        # cuOpt expects an array of single-char byte codes for var types
        dm.set_variable_types(np.asarray(self._var_types, dtype=object).astype(bytes))
        dm.set_maximize(self._sense == Sense.Maximize)
        self._last_dm = dm

        # Settings
        ss = SolverSettings()
        # Time limit precedence: ILPY_CUOPT_TIME_LIMIT env var wins over
        # whatever was passed via set_timeout() (which itself defaults to
        # whatever the caller's ILPSolverConfig.timeout was — typically
        # very large). Letting an env-var override is essential for
        # production deployments that build the solver via tracksdata /
        # third-party code and can't easily reach the set_timeout() call
        # site.
        #
        # Empirical floor for cell-tracking ILPs in heuristics-only mode
        # (cuopt-cu12 == 26.4.x): Papilo presolve alone takes ~91 s, so
        # time_limit < ~120 s frequently returns a trivial / infeasible
        # primal. Recommended production default for MIPs of this shape:
        # 240 s (~1.3x safety margin over the 180s "first usable primal"
        # floor measured on ops0042 A/2: 2.2M nodes / 1.56M edges).
        # See royerlab/hoct_inference PR #5 for the measurement methodology.
        effective_time_limit = self._time_limit
        env_time_limit = os.environ.get("ILPY_CUOPT_TIME_LIMIT")
        if env_time_limit:
            try:
                effective_time_limit = float(env_time_limit)
            except ValueError:
                pass
        if effective_time_limit is not None:
            ss.set_parameter("time_limit", str(effective_time_limit))
        if self._mip_gap_rel is not None:
            ss.set_parameter("mip_relative_gap", str(self._mip_gap_rel))
        if self._mip_gap_abs is not None:
            ss.set_parameter("mip_absolute_gap", str(self._mip_gap_abs))
        if self._verbose:
            # cuOpt's log level varies by release; "log_level" is the
            # documented public knob.
            try:
                ss.set_parameter("log_level", "1")
            except Exception:
                pass

        # Optional escape hatch for advanced tuning. Same idiom as the
        # OPS_CUOPT_EXTRA_PARAMS env var used in downstream consumers.
        if os.environ.get("ILPY_CUOPT_HEURISTICS_ONLY") == "1":
            try:
                ss.set_parameter("mip_heuristics_only", "1")
            except Exception:
                pass
        extra = os.environ.get("ILPY_CUOPT_EXTRA_PARAMS", "")
        for raw_kv in extra.split(","):
            kv_clean = raw_kv.strip()
            if not kv_clean or "=" not in kv_clean:
                continue
            param_name, param_value = kv_clean.split("=", 1)
            try:
                ss.set_parameter(param_name.strip(), param_value.strip())
            except Exception:
                pass

        # Progress events: cuOpt's per-incumbent hook is MILP-only and is
        # invoked from C++ once per new feasible solution. For LP problems
        # (and MIPs that solve entirely during presolve), no incumbent
        # callback fires, so we always emit a terminal "SOLVED" event below
        # to give callers at least one payload per solve.
        is_mip = bool(self._var_types is not None and (self._var_types == b"I").any())

        backend_self = self

        class _IncumbentRelay(GetSolutionCallback):
            """Forward each cuOpt incumbent to ilpy's event-callback hook."""

            def get_solution(
                self,
                solution: Any,
                solution_cost: Any,
                solution_bound: Any,
                user_data: Any,
            ) -> None:
                # cuOpt reports the unshifted objective; add ilpy's
                # objective constant so the value matches Solution.value.
                try:
                    cost = float(solution_cost[0]) + obj_constant
                    bound = float(solution_bound[0]) + obj_constant
                except Exception:
                    return
                denom = max(abs(cost), 1e-10)
                gap = abs(cost - bound) / denom
                backend_self.emit_event_data(
                    {
                        "backend": "cuopt",
                        "event_type": "MIPSOL",
                        "obj": cost,
                        "solution_bound": bound,
                        "gap": gap,
                        "runtime": _time.monotonic() - t0,
                    }
                )

        if is_mip:
            ss.set_mip_callback(_IncumbentRelay(), None)

        # Solve
        t0 = _time.monotonic()
        sol = solver.Solve(dm, ss)
        wall = _time.monotonic() - t0

        native_status = int(sol.get_termination_status())
        status = STATUS_MAP.get(native_status, SolverStatus.OTHER)

        try:
            primal = sol.get_primal_solution()
            variable_values = list(np.asarray(primal, dtype=np.float64))
        except Exception:
            variable_values = [0.0] * n_vars

        try:
            obj_val = float(sol.get_primal_objective()) + obj_constant
        except Exception:
            obj_val = float("nan")

        self.emit_event_data(
            {
                "backend": "cuopt",
                "event_type": "SOLVED",
                "obj": obj_val,
                "status": native_status,
                "runtime": wall,
            }
        )

        return Solution(
            variable_values=variable_values,
            objective_value=obj_val,
            status=status,
            time=wall,
            native_status=sol.get_termination_reason(),
        )

    # --------------------------------------------------------- introspection

    def native_model(self) -> Any:
        return self._last_dm
