
from ._components import Constraint, Constraints, Objective
from ._constants import Relation, Sense, VariableType
from ._solver import Solution, Solver, SolverBackend
from .expressions import Expression, Variable
from .solver_backends import Preference

Maximize = Sense.Maximize
Minimize = Sense.Minimize
