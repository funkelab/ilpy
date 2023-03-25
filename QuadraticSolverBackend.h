#ifndef INFERENCE_QUADRATIC_SOLVER_BACKEND_H__
#define INFERENCE_QUADRATIC_SOLVER_BACKEND_H__

#include "QuadraticObjective.h"
#include "QuadraticConstraint.h"
#include "LinearSolverBackend.h"

class QuadraticSolverBackend : public LinearSolverBackend {

public:

	virtual ~QuadraticSolverBackend() {}

	/**
	 * Set the objective.
	 *
	 * @param objective A quadratic objective.
	 */
	virtual void setObjective(const QuadraticObjective& objective) = 0;

	using LinearSolverBackend::setObjective;

	/**
	 * Add a single constraint.
	 *
	 * @param constraint A quadratic constraints.
	 */
	virtual void addConstraint(const QuadraticConstraint& constraint) = 0;

	using LinearSolverBackend::addConstraint;
};

#endif // INFERENCE_QUADRATIC_SOLVER_BACKEND_H__

