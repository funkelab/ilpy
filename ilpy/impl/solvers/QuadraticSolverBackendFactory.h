#ifndef QUADRATIC_PROGRAM_SOLVER_FACTORY_H__
#define QUADRATIC_PROGRAM_SOLVER_FACTORY_H__

#include <memory>
#include "SolverBackend.h"
#include "BackendPreference.h"

class SolverBackendFactory {

public:

	virtual std::shared_ptr<SolverBackend> createSolverBackend(Preference preference = Any) const = 0;
};

#endif // QUADRATIC_PROGRAM_SOLVER_FACTORY_H__

