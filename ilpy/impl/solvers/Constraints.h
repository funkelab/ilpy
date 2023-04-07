#ifndef INFERENCE_CONSTRAINTS_H__
#define INFERENCE_CONSTRAINTS_H__

#include "Constraint.h"

class Constraints {

	typedef std::vector<Constraint> constraints_type;

public:

	typedef constraints_type::iterator       iterator;

	typedef constraints_type::const_iterator const_iterator;

	/**
	 * Create a new set of constraints and allocate enough memory to hold
	 * 'size' constraints. More or less constraints can be added, but
	 * memory might be wasted (if more allocated then necessary) or unnecessary
	 * reallocations might occur (if more added than allocated).
	 *
	 * @param size The number of constraints to reserve memory for.
	 */
	Constraints(size_t size = 0);

	/**
	 * Remove all constraints from this set of constraints.
	 */
	void clear() { _constraints.clear(); }

	/**
	 * Add a constraint.
	 *
	 * @param constraint The constraint to add.
	 */
	void add(const Constraint& constraint);

	/**
	 * Add a set of constraints.
	 *
	 * @param constraints The set of constraints to add.
	 */
	void addAll(const Constraints& constraints);

	/**
	 * @return The number of constraints in this set.
	 */
	unsigned int size() const { return _constraints.size(); }

	const const_iterator begin() const { return _constraints.begin(); }

	iterator begin() { return _constraints.begin(); }

	const const_iterator end() const { return _constraints.end(); }

	iterator end() { return _constraints.end(); }

	const Constraint& operator[](size_t i) const { return _constraints[i]; }

	Constraint& operator[](size_t i) { return _constraints[i]; }

	/**
	 * Get a linst of indices of constraints that use the given variables.
	 */
	std::vector<unsigned int> getConstraints(const std::vector<unsigned int>& variableIds);

private:

	constraints_type _constraints;
};

#endif // INFERENCE_CONSTRAINTS_H__

