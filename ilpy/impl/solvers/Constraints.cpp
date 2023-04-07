#include "Constraints.h"

Constraints::Constraints(size_t size) {

	_constraints.resize(size);
}

void
Constraints::add(const Constraint& constraint) {

	_constraints.push_back(constraint);
}

void
Constraints::addAll(const Constraints& constraints) {

	_constraints.insert(_constraints.end(), constraints.begin(), constraints.end());
}

std::vector<unsigned int>
Constraints::getConstraints(const std::vector<unsigned int>& variableIds) {

	std::vector<unsigned int> indices;

	for (unsigned int i = 0; i < size(); i++) {

		Constraint& constraint = _constraints[i];

		for (unsigned int v : variableIds) {

			if (constraint.getCoefficients().count(v) != 0) {

				indices.push_back(i);
				break;
			}
		}
	}

	return indices;
}
