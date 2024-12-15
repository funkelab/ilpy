#ifndef SCIP_SOLVER_H__
#define SCIP_SOLVER_H__

#include <string>

#include <scip/scip.h>

#include "Constraints.h"
#include "Objective.h"
#include "SolverBackend.h"
#include "Sense.h"
#include "Solution.h"

/**
 * Scip interface to solve the following (integer) quadratic program:
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
class ScipBackend : public SolverBackend {

public:

	ScipBackend();

	virtual ~ScipBackend();

    std::string getName() const override {
        return "Scip";
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

	void setTimeout(double timeout) override;

	void setOptimalityGap(double gap, bool absolute=false) override;

	void setNumThreads(unsigned int numThreads) override;

	bool solve(Solution& solution, std::string& message) override;

	std::string solve(Solution& solution) {

		std::string message;
		solve(solution, message);
		return message;
	}

	/**
	 * Enable solver output.
	 */
	void setVerbose(bool verbose) override;

private:

	//////////////
	// internal //
	//////////////

	void addMulEqualConstraint(unsigned int i, unsigned int j, SCIP_VAR* z_ij);

	void freeVariables();

	void freeConstraints();

	SCIP_VARTYPE scipVarType(VariableType type, double& lb, double& ub);

	// size of a and x
	unsigned int _numVariables;

	SCIP* _scip;

	std::vector<SCIP_VAR*> _variables;

	std::vector<SCIP_CONS*> _constraints;
};

// Factory function to create ScipBackend
extern "C" SolverBackend* createSolverBackend();

#endif // SCIP_SOLVER_H__



