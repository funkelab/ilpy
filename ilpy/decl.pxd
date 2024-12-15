from libcpp cimport bool
from libcpp.string cimport string
from libcpp.memory cimport shared_ptr
from libcpp.map cimport map
from libcpp.pair cimport pair
from libcpp.vector cimport vector
from cpython.object cimport PyObject

cdef extern from "impl/solvers/Relation.h":
    cdef enum Relation:
        LessEqual
        Equal
        GreaterEqual

cdef extern from "impl/solvers/VariableType.h":
    cdef enum VariableType:
        Continuous
        Integer
        Binary

cdef extern from "impl/solvers/Sense.h":
    cdef enum Sense:
        Minimize
        Maximize

cdef extern from "impl/solvers/BackendPreference.h":
    cdef enum Preference:
        Any
        Scip
        Gurobi
        Cplex

cdef extern from "impl/solvers/Solution.cpp":
    pass

cdef extern from "impl/solvers/Solution.h":
    cdef cppclass Solution:
        Solution(unsigned int) except +
        void resize(unsigned int)
        unsigned int size()
        double& operator[](unsigned int i)
        void setValue(double value)
        double getValue()

cdef extern from "impl/solvers/Objective.cpp":
    pass

cdef extern from "impl/solvers/Objective.h":
    cdef cppclass Objective:
        Objective() except +
        Objective(unsigned int) except +
        void setConstant(double)
        double getConstant()
        void setCoefficient(unsigned int, double)
        const vector[double]& getCoefficients()
        void setQuadraticCoefficient(unsigned int, unsigned int, double)
        const map[pair[unsigned int, unsigned int], double]& getQuadraticCoefficients()
        void setSense(Sense)
        Sense getSense()
        void resize(unsigned int)
        unsigned int size()

cdef extern from "impl/solvers/Constraint.cpp":
    pass

cdef extern from "impl/solvers/Constraint.h":
    cdef cppclass Constraint:
        Constraint() except +
        void setCoefficient(unsigned int, double)
        const map[unsigned int, double]& getCoefficients()
        void setQuadraticCoefficient(unsigned int, unsigned int, double)
        const map[pair[unsigned int, unsigned int], double]& getQuadraticCoefficients()
        void setRelation(Relation)
        void setValue(double)
        Relation getRelation()
        double getValue()
        bool isViolated(const Solution&)

cdef extern from "impl/solvers/Constraints.cpp":
    pass

cdef extern from "impl/solvers/Constraints.h":
    cdef cppclass Constraints:
        Constraints() except +
        void clear()
        void add(Constraint&)
        void addAll(Constraints&)
        unsigned int size()

cdef extern from "impl/solvers/SolverBackend.h":
    cdef cppclass SolverBackend:
        void initialize(
            unsigned int, VariableType, map[unsigned int, VariableType]&
        ) except +
        string getName()
        void setObjective(Objective&)
        void setConstraints(Constraints&)
        void addConstraint(Constraint&)
        void setTimeout(double)
        void setOptimalityGap(double, bool)
        void setNumThreads(unsigned int)
        void setVerbose(bool)
        bool solve(Solution& solution, string& message) except +
        void setEventCallback(PyObject* callback)


cdef extern from "impl/solvers/SolverFactory.cpp":
    pass

cdef extern from "impl/solvers/SolverFactory.h":
    cdef cppclass SolverFactory:
        shared_ptr[SolverBackend] createSolverBackend(Preference) except +
