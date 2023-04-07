#ifndef INFERENCE_QUADRATIC_CONSTRAINT_H__
#define INFERENCE_QUADRATIC_CONSTRAINT_H__

#include <map>
#include <ostream>

#include "Relation.h"
#include "Solution.h"
/**
 * A sparse quadratic constraint.
 */
class Constraint {

public:

	Constraint();

	void setCoefficient(unsigned int varNum, double coef);

	void setQuadraticCoefficient(unsigned int varNum1, unsigned int varNum2, double coef);

	void setRelation(Relation relation);

	void setValue(double value);

	const std::map<unsigned int, double>& getCoefficients() const;

	const std::map<std::pair<unsigned int, unsigned int>, double>& getQuadraticCoefficients() const;

	const Relation& getRelation() const;

	double getValue() const;

    bool isViolated(const Solution & solution);

private:

	std::map<unsigned int, double> _coefs;

	std::map<std::pair<unsigned int, unsigned int>, double> _quadraticCoefs;

	Relation _relation;

	double _value;
};

std::ostream& operator<<(std::ostream& out, const Constraint& constraint);

#endif // INFERENCE_QUADRATIC_CONSTRAINT_H__

