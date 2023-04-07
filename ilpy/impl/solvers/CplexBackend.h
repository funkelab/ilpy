#ifndef CPLEX_SOLVER_H__
#define CPLEX_SOLVER_H__

#ifdef HAVE_CPLEX



#include <string>
#include <vector>

#include <ilcplex/ilocplex.h>

#include "LinearConstraints.h"
#include "QuadraticObjective.h"
#include "QuadraticSolverBackend.h"
#include "Sense.h"
#include "Solution.h"



/**
 * Cplex interface to solve the following (integer) quadratic program:
 *
 * min  <a,x> + xQx
 * s.t. Ax  == b
 *      Cx  <= d
 *      optionally: x_i \in {0,1} for all i
 *
 * Where (A,b) describes all linear equality constraints, (C,d) all linear
 * inequality constraints and x is the solution vector. a is a real-valued
 * vector denoting the coefficients of the objective and Q a PSD matrix giving
 * the quadratic coefficients of the objective.
 */
class CplexBackend : public QuadraticSolverBackend {

public:

    struct Parameter {

        Parameter() :
            mipGap(0.0001),
            absoluteGap(false),
            mipFocus(0),
            numThreads(0),
            verbose(false) {}

        // The Gurobi relative optimality gap.
        double mipGap;
        bool absoluteGap;

        // The Gurobi MIP focus: 0 = balanced, 1 = feasible solutions, 2 =
        // optimal solution, 3 = bound.
        unsigned int mipFocus;

        // The number of threads to be used by Gurobi. The default (0) uses all
        // available CPUs.
        unsigned int numThreads;

        // Show the gurobi output.
        bool verbose;
    };

    CplexBackend(const Parameter& parameter = Parameter());

    virtual ~CplexBackend();

    ///////////////////////////////////
    // solver backend implementation //
    ///////////////////////////////////

    void initialize(
            unsigned int numVariables,
            VariableType variableType);

    void initialize(
            unsigned int                                numVariables,
            VariableType                                defaultVariableType,
            const std::map<unsigned int, VariableType>& specialVariableTypes);

    void setObjective(const LinearObjective& objective);

    void setObjective(const QuadraticObjective& objective);

    void setConstraints(const LinearConstraints& constraints);

    void addConstraint(const LinearConstraint& constraint);

    void setTimeout(double timeout) { timeout_ = timeout; }

    void setOptimalityGap(double gap, bool absolute=false) {

        _parameter.mipGap = gap;
        _parameter.absoluteGap = absolute;
    }

    void setNumThreads(unsigned int numThreads);

    bool solve(Solution& solution,/* double& value, */ std::string& message);

    std::string solve(Solution& solution) {

        std::string message;
        solve(solution, message);
        return message;
    }

private:

    //////////////
    // internal //
    //////////////

    // set the optimality gap
    void setMIPGap(double gap, bool absolute);

    // set the mpi focus
    void setMIPFocus(unsigned int focus);

    // create a CPLEX constraint from a linear constraint
    IloRange createConstraint(const LinearConstraint &constraint);

    /**
     * Enable solver output.
     */
    void setVerbose(bool verbose);

    // size of a and x
    unsigned int _numVariables;

    // rows in A
    unsigned int _numEqConstraints;

    // rows in C
    unsigned int _numIneqConstraints;

    Parameter _parameter;

    // the verbosity of the output
    int _verbosity;

    // a value by which to scale the objective
    double _scale;

    // Objective, constraints and cplex environment:
    IloEnv env_;
    IloModel model_;
    IloNumVarArray x_;
    IloRangeArray c_;
    IloObjective obj_;
    IloNumArray sol_;
    IloCplex cplex_;
    double constValue_;

    typedef std::vector<IloExtractable> ConstraintVector;
    ConstraintVector _constraints;

    // are we in the first run
    bool firstRun_;

    double timeout_;
};


#endif // HAVE_CPLEX
#endif // CPLEX_SOLVER_H__
