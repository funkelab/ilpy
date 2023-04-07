#include "QuadraticObjective.h"

QuadraticObjective::QuadraticObjective(unsigned int size) :
	_sense(Minimize),
	_constant(0) {

	resize(size);
}

void
QuadraticObjective::setConstant(double constant) {

	_constant = constant;
}

double
QuadraticObjective::getConstant() const {

	return _constant;
}

void
QuadraticObjective::setCoefficient(unsigned int varNum, double coef) {

	if (varNum >= size())
		resize(varNum + 1);

	_coefs[varNum] = coef;
}

const std::vector<double>&
QuadraticObjective::getCoefficients() const {

	return _coefs;
}

void
QuadraticObjective::setQuadraticCoefficient(unsigned int varNum1, unsigned int varNum2, double coef) {

	if (coef == 0) {

		_quadraticCoefs.erase(_quadraticCoefs.find(std::make_pair(varNum1, varNum2)));

	} else {

		_quadraticCoefs[std::make_pair(varNum1, varNum2)] = coef;
	}
}

const std::map<std::pair<unsigned int, unsigned int>, double>&
QuadraticObjective::getQuadraticCoefficients() const {

	return _quadraticCoefs;
}

void
QuadraticObjective::setSense(Sense sense) {

	_sense = sense;
}

Sense
QuadraticObjective::getSense() const {

	return _sense;
}

void
QuadraticObjective::resize(unsigned int size) {

	_coefs.resize(size, 0.0);
}

std::ostream& operator<<(std::ostream& out, const QuadraticObjective& objective) {

	for (unsigned int i = 0; i < objective.size(); i++)
		out << objective.getCoefficients()[i] << "*" << i << " ";

	typedef std::map<std::pair<unsigned int, unsigned int>, double>::value_type pair_t;
	for (pair_t p : objective.getQuadraticCoefficients())
		out << p.second << "*" << p.first.first << "*" << p.first.second << " ";

	return out;
}
