#ifndef INFERENCE_QUADRATIC_SOLVER_BACKEND_H__
#define INFERENCE_QUADRATIC_SOLVER_BACKEND_H__

#include "Objective.h"
#include "Constraint.h"

class SolverBackend {

public:

	virtual ~SolverBackend() {}

	/**
	 * Initialise the linear solver for the given type of variables.
	 *
	 * @param numVariables The number of variables in the problem.
	 * @param variableType The type of the variables (Continuous, Integer,
	 *                     Binary).
	 */
	virtual void initialize(
			unsigned int numVariables,
			VariableType variableType) = 0;

	/**
	 * Initialise the linear solver for the given type of variables.
	 *
	 * @param numVariables
	 *             The number of variables in the problem.
	 * 
	 * @param defaultVariableType
	 *             The default type of the variables (Continuous, Integer, 
	 *             Binary).
	 *
	 * @param specialVariableTypes
	 *             A map of variable numbers to variable types to override the 
	 *             default.
	 */
	virtual void initialize(
			unsigned int                                numVariables,
			VariableType                                defaultVariableType,
			const std::map<unsigned int, VariableType>& specialVariableTypes) = 0;

	/**
	 * Set the objective.
	 *
	 * @param objective A linear objective.
	 */
	virtual void setObjective(const Objective& objective) = 0;

	/**
	 * Set the linear (in)equality constraints.
	 *
	 * @param constraints A set of linear constraints.
	 */
	virtual void setConstraints(const Constraints& constraints) = 0;

	/**
	 * Add a single constraint.
	 *
	 * @param constraint A linear constraints.
	 */
	virtual void addConstraint(const Constraint& constraint) = 0;

	/**
	 * Set a timeout in seconds for subsequent solve calls.
	 */
	virtual void setTimeout(double timeout) = 0;

	/**
	 * Set the solver's optimality gap. The solver will terminate with an 
	 * "optimal" solution as soon as the gap between the upper and lower bound 
	 * is less than the given value times the upper bound.
	 *
	 * @param gap
	 *             The optimality gap.
	 *
	 * @param absolute
	 *             If set to true, a solution is considered optimal if the gap 
	 *             between the upper and lower bound is smaller than the given 
	 *             value.
	 */
	virtual void setOptimalityGap(double gap, bool absolute=false) = 0;

	/**
	 * Set the number of threads the solver can use.
	 *
	 * @param numThreads
	 *             The number of threads to use. Defaults to 0, which leaves the 
	 *             decision to the solver.
	 */
	virtual void setNumThreads(unsigned int numThreads) = 0;

	/**
	 * Turn verbose logging on or off.
	 *
	 * @param verbose
	 *             If set to true, verbose logging is enabled.
	 */
        virtual void setVerbose(bool verbose) = 0;

	/**
	 * Solve the problem.
	 *
	 * @param solution A solution object to write the solution to.
	 * @param value The optimal value of the objective.
	 * @param message A status message from the solver.
	 * @return true, if the optimal value was found.
	 */
	virtual bool solve(Solution& solution, std::string& message) = 0;
};

#endif // INFERENCE_QUADRATIC_SOLVER_BACKEND_H__

