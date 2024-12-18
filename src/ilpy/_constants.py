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
