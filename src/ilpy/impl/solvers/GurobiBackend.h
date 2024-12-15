#ifndef GUROBI_SOLVER_H__
#define GUROBI_SOLVER_H__

#include <string>

extern "C" {
#include <gurobi_c.h>
}

#include "Constraints.h"
#include "Objective.h"
#include "SolverBackend.h"
#include "Sense.h"
#include "Solution.h"

/**
 * Gurobi interface to solve the following (integer) quadratic program:
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
class GurobiBackend : public SolverBackend {

public:

	GurobiBackend();

	virtual ~GurobiBackend();

    std::string getName() const override {
        return "Gurobi";
    }

	///////////////////////////////////
	// solver backend implementation //
	///////////////////////////////////

	void initialize(
			unsigned int numVariables,
			VariableType variableType) override;

	void initialize(
			unsigned int                                numVariables,
			VariableType                                defaultVariableType,
			const std::map<unsigned int, VariableType>& specialVariableTypes) override;

	void setObjective(const Objective& objective) override;

	void setConstraints(const Constraints& constraints) override;

	void addConstraint(const Constraint& constraint) override;

	void setTimeout(double timeout) override { _timeout = timeout; }

	void setOptimalityGap(double gap, bool absolute=false) override {

		_gap = gap;
		_absoluteGap = absolute;
	}

	void setNumThreads(unsigned int numThreads) override;

	bool solve(Solution& solution, std::string& message) override;

	std::string solve(Solution& solution) { 

		std::string message;
		solve(solution, message);
		return message;
	}

	// enable solver output
	void setVerbose(bool verbose) override;

private:

	//////////////
	// internal //
	//////////////

	// dump the current problem to a file
	void dumpProblem(std::string filename);

	// set the mpi focus
	void setMIPFocus(unsigned int focus);


	// check error status and throw exception, used by our macro GRB_CHECK
	void grbCheck(const char* call, const char* file, int line, int error);

	// size of a and x
	unsigned int _numVariables;

	// the GRB environment
	GRBenv* _env;

	// the GRB model containing the objective and constraints
	GRBmodel* _model;

	double _timeout;

	double _gap;

	bool _absoluteGap;
};

// Factory function to create GurobiBackend
extern "C" SolverBackend* createSolverBackend();

#endif // GUROBI_SOLVER_H__


