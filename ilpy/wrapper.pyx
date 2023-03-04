# distutils: language = c++

from libc.stdint cimport uint32_t
from libcpp.memory cimport shared_ptr
from libcpp.map cimport map as cppmap
from libcpp.string cimport string
from cython.operator cimport dereference as deref
cimport decl

####################################
# Enums                            #
####################################

cpdef enum VariableType:
    Continuous = <uint32_t> decl.Continuous
    Integer = <uint32_t> decl.Integer
    Binary = <uint32_t> decl.Binary

cpdef enum Sense:
    Minimize = <uint32_t> decl.Minimize
    Maximize = <uint32_t> decl.Maximize

cpdef enum Relation:
    LessEqual = <uint32_t> decl.LessEqual
    Equal = <uint32_t> decl.Equal
    GreaterEqual = <uint32_t> decl.GreaterEqual

cpdef enum Preference:
    Any = <uint32_t> decl.Any
    Scip = <uint32_t> decl.Scip
    Gurobi = <uint32_t> decl.Gurobi
    Cplex = <uint32_t> decl.Cplex

####################################
# Classes                          #
####################################

cdef class Solution:

    cdef decl.Solution* p

    def __cinit__(self, size):
        self.p = new decl.Solution(size)

    def __dealloc__(self):
        del self.p

    def __len__(self):
        return self.p.size()

    def __getitem__(self, i):
        if i < 0 or i >= self.p.size():
            raise IndexError()
        return self.p[0][i]

    def __setitem__(self, i, value):
        if i < 0 or i >= self.p.size():
            raise IndexError()
        self.p[0][i] = value

    def resize(self, size):
        self.p.resize(size)

    def get_value(self):
        return self.p.getValue()

    def set_value(self, value):
        self.p.setValue(value)

cdef class QuadraticObjective:

    cdef decl.QuadraticObjective* p

    def __cinit__(self, size = 0):
        self.p = new decl.QuadraticObjective(size)

    def __dealloc__(self):
        del self.p

    def set_constant(self, value):
        self.p.setConstant(value)

    def get_constant(self):
        return self.p.getConstant()

    def set_coefficient(self, i, value):
        self.p.setCoefficient(i, value)

    def get_coefficients(self):
        return self.p.getCoefficients()

    def set_quadratic_coefficient(self, i, j, value):
        self.p.setQuadraticCoefficient(i, j, value)

    def set_sense(self, sense):
        self.p.setSense(sense)

    def get_sense(self):
        return Sense(self.p.getSense())

    def resize(self, size):
        self.p.resize(size)

    def __len__(self):
        return self.p.size()

cdef class LinearObjective:

    cdef decl.LinearObjective* p

    def __cinit__(self, size = 0):
        self.p = new decl.LinearObjective(size)

    def __dealloc__(self):
        del self.p

    def set_constant(self, value):
        self.p.setConstant(value)

    def get_constant(self):
        return self.p.getConstant()

    def set_coefficient(self, i, value):
        self.p.setCoefficient(i, value)

    def get_coefficients(self):
        return self.p.getCoefficients()

    def set_sense(self, sense):
        self.p.setSense(sense)

    def get_sense(self):
        return Sense(self.p.getSense())

    def resize(self, size):
        self.p.resize(size)

    def __len__(self):
        return self.p.size()

cdef class LinearConstraint:

    cdef decl.LinearConstraint* p

    def __cinit__(self):
        self.p = new decl.LinearConstraint()

    def __dealloc__(self):
        del self.p

    def set_coefficient(self, i, value):
        self.p.setCoefficient(i, value)

    def get_coefficients(self):
        return self.p.getCoefficients()

    def set_relation(self, relation):
        self.p.setRelation(relation)

    def set_value(self, value):
        self.p.setValue(value)

    def get_relation(self):
        return Relation(self.p.getRelation())

    def get_value(self):
        return self.p.getValue()

    def is_violated(self, Solution solution):
        return self.p.isViolated(solution.p[0])

cdef class LinearConstraints:

    cdef decl.LinearConstraints* p

    def __cinit__(self):
        self.p = new decl.LinearConstraints()

    def __dealloc__(self):
        del self.p

    def clear(self):
        self.p.clear()

    def add(self, LinearConstraint constraint):
        self.p.add(constraint.p[0])

    def add_all(self, LinearConstraints constraints):
        self.p.addAll(constraints.p[0])

    def __len__(self):
        return self.p.size()

cdef class LinearSolver:

    cdef shared_ptr[decl.LinearSolverBackend] p
    cdef unsigned int num_variables

    def __cinit__(
            self,
            num_variables,
            default_variable_type,
            dict variable_types=None,
            Preference preference=Preference.Any):
        cdef decl.SolverFactory factory
        cdef cppmap[unsigned int, decl.VariableType] vtypes
        if variable_types is not None:
            for k, v in variable_types.items():
                vtypes[k] = v
        self.p = factory.createLinearSolverBackend(preference)
        self.num_variables = num_variables
        deref(self.p).initialize(num_variables, default_variable_type, vtypes)

    def set_objective(self, LinearObjective objective):
        deref(self.p).setObjective(objective.p[0])

    def set_constraints(self, LinearConstraints constraints):
        deref(self.p).setConstraints(constraints.p[0])

    def add_constraint(self, LinearConstraint constraint):
        deref(self.p).addConstraint(constraint.p[0])

    def set_timeout(self, timeout):
        deref(self.p).setTimeout(timeout)

    def set_optimality_gap(self, gap, absolute=False):
        deref(self.p).setOptimalityGap(gap, absolute)

    def set_num_threads(self, num_threads):
        deref(self.p).setNumThreads(num_threads)

    def set_verbose(self, verbose):
        deref(self.p).setVerbose(verbose)

    def solve(self):
        solution = Solution(self.num_variables)
        cdef string message
        deref(self.p).solve(solution.p[0], message)
        return solution, message

cdef class QuadraticSolver:

    cdef shared_ptr[decl.QuadraticSolverBackend] p
    cdef unsigned int num_variables

    def __cinit__(
            self,
            num_variables,
            default_variable_type,
            dict variable_types=None,
            Preference preference=Preference.Any):
        cdef decl.SolverFactory factory
        cdef cppmap[unsigned int, decl.VariableType] vtypes
        if variable_types is not None:
            for k, v in variable_types.items():
                vtypes[k] = v
        self.p = factory.createQuadraticSolverBackend(preference)
        self.num_variables = num_variables
        deref(self.p).initialize(num_variables, default_variable_type, vtypes)

    def set_objective(self, QuadraticObjective objective):
        deref(self.p).setObjective(objective.p[0])

    def set_constraints(self, LinearConstraints constraints):
        deref(self.p).setConstraints(constraints.p[0])

    def add_constraint(self, LinearConstraint constraint):
        deref(self.p).addConstraint(constraint.p[0])

    def set_timeout(self, timeout):
        deref(self.p).setTimeout(timeout)

    def set_optimality_gap(self, gap, absolute=False):
        deref(self.p).setOptimalityGap(gap, absolute)

    def set_num_threads(self, num_threads):
        deref(self.p).setNumThreads(num_threads)

    def solve(self):
        solution = Solution(self.num_variables)
        cdef string message
        deref(self.p).solve(solution.p[0], message)
        return solution, message
