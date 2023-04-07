#include "QuadraticConstraint.h"

QuadraticConstraint::QuadraticConstraint() :
	_relation(LessEqual) {}

void
QuadraticConstraint::setCoefficient(unsigned int varNum, double coef) {

	if (coef == 0) {

		std::map<unsigned int, double>::iterator i = _coefs.find(varNum);
		if (i != _coefs.end())
			_coefs.erase(_coefs.find(varNum));

	} else {

		_coefs[varNum] = coef;
	}
}

void
QuadraticConstraint::setQuadraticCoefficient(unsigned int varNum1, unsigned int varNum2, double coef) {

	if (coef == 0) {

		_quadraticCoefs.erase(_quadraticCoefs.find(std::make_pair(varNum1, varNum2)));

	} else {

		_quadraticCoefs[std::make_pair(varNum1, varNum2)] = coef;
	}
}

void
QuadraticConstraint::setRelation(Relation relation) {

	_relation = relation;
}

bool QuadraticConstraint::isViolated(const Solution & solution){

    double s = 0;

    for(const auto & kv : _coefs){
        const auto var = kv.first;
        const auto coef = kv.second;
        const auto sol = solution[var];
        s+= coef*sol;
    }
    if(_relation == LessEqual){
        return s > _value;
    }
    else if(_relation == GreaterEqual){
        return s < _value;
    }
    else{
        return s != _value;
    }
}


void
QuadraticConstraint::setValue(double value) {

	_value = value;
}

const std::map<unsigned int, double>&
QuadraticConstraint::getCoefficients() const {

	return _coefs;
}

const std::map<std::pair<unsigned int, unsigned int>, double>&
QuadraticConstraint::getQuadraticCoefficients() const {

	return _quadraticCoefs;
}

const Relation&
QuadraticConstraint::getRelation() const {

	return _relation;
}

double
QuadraticConstraint::getValue() const {

	return _value;
}

std::ostream& operator<<(std::ostream& out, const QuadraticConstraint& constraint) {

	typedef std::map<unsigned int, double>::value_type pair_t;
	for (const pair_t& pair : constraint.getCoefficients())
		out << pair.second << "*" << pair.first << " ";

	typedef std::map<std::pair<unsigned int, unsigned int>, double>::value_type pair2_t;
	for (pair2_t p : constraint.getQuadraticCoefficients())
		out << p.second << "*" << p.first.first << "*" << p.first.second << " ";

	out << (constraint.getRelation() == LessEqual ? "<=" : (constraint.getRelation() == GreaterEqual ? ">=" : "=="));

	out << " " << constraint.getValue();

	return out;
}
