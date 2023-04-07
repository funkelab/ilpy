#include "Constraint.h"

Constraint::Constraint() :
	_relation(LessEqual) {}

void
Constraint::setCoefficient(unsigned int varNum, double coef) {

	if (coef == 0) {

		_coefs.erase(varNum);

	} else {

		_coefs[varNum] = coef;
	}
}

void
Constraint::setQuadraticCoefficient(unsigned int varNum1, unsigned int varNum2, double coef) {

	if (coef == 0) {

		_quadraticCoefs.erase(std::make_pair(varNum1, varNum2));

	} else {

		_quadraticCoefs[std::make_pair(varNum1, varNum2)] = coef;
	}
}

void
Constraint::setRelation(Relation relation) {

	_relation = relation;
}

bool Constraint::isViolated(const Solution & solution){

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
Constraint::setValue(double value) {

	_value = value;
}

const std::map<unsigned int, double>&
Constraint::getCoefficients() const {

	return _coefs;
}

const std::map<std::pair<unsigned int, unsigned int>, double>&
Constraint::getQuadraticCoefficients() const {

	return _quadraticCoefs;
}

const Relation&
Constraint::getRelation() const {

	return _relation;
}

double
Constraint::getValue() const {

	return _value;
}

std::ostream& operator<<(std::ostream& out, const Constraint& constraint) {

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
