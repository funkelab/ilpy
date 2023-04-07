#ifndef LINEAR_PROGRAM_SOLVER_FACTORY_H__
#define LINEAR_PROGRAM_SOLVER_FACTORY_H__

#include <memory>
#include "BackendPreference.h"

// forward declaration
class SolverBackend;

class SolverBackendFactory {

public:

	virtual std::shared_ptr<SolverBackend> createSolverBackend(Preference preference = Any) const = 0;
};

#endif // LINEAR_PROGRAM_SOLVER_FACTORY_H__

