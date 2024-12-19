from __future__ import annotations

from enum import Enum, IntEnum, auto


class VariableType(IntEnum):
    Continuous = auto()
    Integer = auto()
    Binary = auto()


class Sense(IntEnum):
    Minimize = auto()
    Maximize = auto()


class Relation(IntEnum):
    LessEqual = auto()
    Equal = auto()
    GreaterEqual = auto()


class SolverStatus(Enum):
    UNKNOWN = "unknown"
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    INF_OR_UNBOUNDED = "infeasible_or_unbounded"
    TIMELIMIT = "time_limit"
    NODELIMIT = "node_limit"
    SOLUTIONLIMIT = "solution_limit"
    USERINTERRUPT = "user_interrupt"
    NUMERIC = "numeric_issue"
    SUBOPTIMAL = "suboptimal"
    OTHER = "other"

# Gurobi Status	        PySCIPOpt Status	        Meaning
# GRB.LOADED	        SCIP_STATUS_UNKNOWN	        Model loaded but not optimized yet.
# GRB.OPTIMAL	        SCIP_STATUS_OPTIMAL	        Optimal solution found.
# GRB.INFEASIBLE	    SCIP_STATUS_INFEASIBLE	    Model proven infeasible.
# GRB.UNBOUNDED	        SCIP_STATUS_UNBOUNDED	    Model proven unbounded.
# GRB.INF_OR_UNBD	    SCIP_STATUS_INFORUNBD	    Infeasible or unbounded.
# GRB.TIME_LIMIT	    SCIP_STATUS_TIMELIMIT	    Time limit reached.
# GRB.NODE_LIMIT	    SCIP_STATUS_NODELIMIT	    Node limit reached.
# GRB.SOLUTION_LIMIT	SCIP_STATUS_SOLLIMIT	    Solution limit reached.
# GRB.INTERRUPTED	    SCIP_STATUS_USERINTERRUPT	Optimization interrupted by user.
# GRB.NUMERIC	        SCIP_STATUS_UNKNOWN	Numerical issues; use getStatusDesc().
