from libcpp cimport bool
from libcpp.string cimport string
from libcpp.memory cimport shared_ptr
from libcpp.map cimport map
from libcpp.pair cimport pair
from libcpp.vector cimport vector

cdef extern from 'impl/solvers/Relation.h':
    cdef enum Relation:
        LessEqual
        Equal
        GreaterEqual

cdef extern from 'impl/solvers/VariableType.h':
    cdef enum VariableType:
        Continuous
        Integer
        Binary

cdef extern from 'impl/solvers/Sense.h':
    cdef enum Sense:
        Minimize
        Maximize

cdef extern from 'impl/solvers/BackendPreference.h':
    cdef enum Preference:
        Any
        Scip
        Gurobi
        Cplex

cdef extern from 'impl/solvers/Solution.cpp':
    pass

cdef extern from 'impl/solvers/Solution.h':
    cdef cppclass Solution:
        Solution(unsigned int) except +
        void resize(unsigned int)
        unsigned int size()
        double& operator[](unsigned int i)
        void setValue(double value)
        double getValue()

cdef extern from 'impl/solvers/QuadraticObjective.cpp':
    pass

cdef extern from 'impl/solvers/QuadraticObjective.h':
    cdef cppclass QuadraticObjective:
        QuadraticObjective() except +
        QuadraticObjective(unsigned int) except +
        void setConstant(double)
        double getConstant()
        void setCoefficient(unsigned int, double)
        const vector[double]& getCoefficients()
        void setQuadraticCoefficient(unsigned int, unsigned int, double)
        void setSense(Sense)
        Sense getSense()
        void resize(unsigned int)
        unsigned int size()

cdef extern from 'impl/solvers/LinearObjective.h':
    cdef cppclass LinearObjective:
        LinearObjective() except +
        LinearObjective(unsigned int) except +
        void setConstant(double)
        double getConstant()
        void setCoefficient(unsigned int, double)
        const vector[double]& getCoefficients()
        void setSense(Sense)
        Sense getSense()
        void resize(unsigned int)
        unsigned int size()

cdef extern from 'impl/solvers/QuadraticConstraint.cpp':
    pass

cdef extern from 'impl/solvers/QuadraticConstraint.h':
    cdef cppclass QuadraticConstraint:
        QuadraticConstraint() except +
        void setCoefficient(unsigned int, double)
        const map[unsigned int, double]& getCoefficients()
        void setQuadraticCoefficient(unsigned int, unsigned int, double)
        const map[pair[unsigned int, unsigned int], double]& getQuadraticCoefficients()
        void setRelation(Relation)
        void setValue(double)
        Relation getRelation()
        double getValue()
        bool isViolated(const Solution&)

cdef extern from 'impl/solvers/LinearConstraint.h':
    cdef cppclass LinearConstraint:
        LinearConstraint() except +
        void setCoefficient(unsigned int, double)
        const map[unsigned int, double]& getCoefficients()
        void setRelation(Relation)
        void setValue(double)
        Relation getRelation()
        double getValue()
        bool isViolated(const Solution&)

cdef extern from 'impl/solvers/LinearConstraints.cpp':
    pass

cdef extern from 'impl/solvers/LinearConstraints.h':
    cdef cppclass LinearConstraints:
        LinearConstraints() except +
        void clear()
        void add(LinearConstraint&)
        void addAll(LinearConstraints&);
        unsigned int size()

cdef extern from 'impl/solvers/LinearSolverBackend.h':
    cdef cppclass LinearSolverBackend:
        void initialize(unsigned int, VariableType, map[unsigned int, VariableType]&) except +
        void setObjective(LinearObjective&)
        void setConstraints(LinearConstraints&)
        void addConstraint(LinearConstraint&)
        void setTimeout(double)
        void setOptimalityGap(double, bool)
        void setNumThreads(unsigned int)
        void setVerbose(bool)
        bool solve(Solution& solution, string& message)

cdef extern from 'impl/solvers/QuadraticSolverBackend.h':
    cdef cppclass QuadraticSolverBackend:
        void initialize(unsigned int, VariableType, map[unsigned int, VariableType]&) except +
        void setObjective(QuadraticObjective&)
        void setConstraints(LinearConstraints&)
        void addConstraint(QuadraticConstraint&)
        void setTimeout(double)
        void setOptimalityGap(double, bool)
        void setNumThreads(unsigned int)
        void setVerbose(bool)
        bool solve(Solution& solution, string& message)

cdef extern from 'impl/solvers/ScipBackend.cpp':
    pass

cdef extern from 'impl/solvers/GurobiBackend.cpp':
    pass

cdef extern from 'impl/solvers/SolverFactory.cpp':
    pass

cdef extern from 'impl/solvers/SolverFactory.h':
    cdef cppclass SolverFactory:
        shared_ptr[LinearSolverBackend] createLinearSolverBackend(Preference) except +
        shared_ptr[QuadraticSolverBackend] createQuadraticSolverBackend(Preference) except +
