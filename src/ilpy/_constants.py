from __future__ import annotations

from enum import Enum, IntEnum, auto


class VariableType(IntEnum):
    """Type of a decision variable in an optimization problem."""

    Continuous = auto()
    """A real-valued variable."""
    Integer = auto()
    """An integer-valued variable."""
    Binary = auto()
    """A variable restricted to 0 or 1."""


class Sense(IntEnum):
    """Direction of an objective function."""

    Minimize = auto()
    """Minimize the objective."""
    Maximize = auto()
    """Maximize the objective."""


class Relation(IntEnum):
    """Relation used in a linear constraint."""

    LessEqual = auto()
    """Left-hand side is less than or equal to the right-hand side."""
    Equal = auto()
    """Left-hand side equals the right-hand side."""
    GreaterEqual = auto()
    """Left-hand side is greater than or equal to the right-hand side."""


class SolverStatus(Enum):
    """Normalized solver status across backends."""

    UNKNOWN = "unknown"
    """Model loaded but not optimized yet."""
    OPTIMAL = "optimal"
    """Optimal solution found."""
    INFEASIBLE = "infeasible"
    """Model proven infeasible."""
    UNBOUNDED = "unbounded"
    """Model proven unbounded."""
    INF_OR_UNBOUNDED = "infeasible_or_unbounded"
    """Model infeasible or unbounded."""
    TIMELIMIT = "time_limit"
    """Time limit reached before proving optimality."""
    NODELIMIT = "node_limit"
    """Node limit reached before proving optimality."""
    SOLUTIONLIMIT = "solution_limit"
    """Solution limit reached."""
    USERINTERRUPT = "user_interrupt"
    """Optimization was interrupted by the user."""
    NUMERIC = "numeric_issue"
    """Numerical issues encountered by the solver."""
    SUBOPTIMAL = "suboptimal"
    """A feasible but not provably optimal solution was returned."""
    OTHER = "other"
    """Status not otherwise classified."""


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
