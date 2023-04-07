#ifndef INFERENCE_DEFAULT_FACTORY_H__
#define INFERENCE_DEFAULT_FACTORY_H__

#include <memory>
#include "SolverBackendFactory.h"

class SolverFactory : public SolverBackendFactory {

public:

	std::shared_ptr<SolverBackend> createSolverBackend(Preference preference = Any) const;
};

#endif // INFERENCE_DEFAULT_FACTORY_H__

