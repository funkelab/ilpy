#ifndef INFERENCE_LINEAR_CONSTRAINT_H__
#define INFERENCE_LINEAR_CONSTRAINT_H__

#include "QuadraticConstraint.h"

/**
 * A sparse linear constraint.
 */
class LinearConstraint : public QuadraticConstraint {

public:

	explicit LinearConstraint() : QuadraticConstraint() {}

private:

	using QuadraticConstraint::setQuadraticCoefficient;
};

#endif // INFERENCE_LINEAR_CONSTRAINT_H__

