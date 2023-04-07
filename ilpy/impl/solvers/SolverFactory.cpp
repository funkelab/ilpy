#include "SolverFactory.h"

#include <config.h>
#include <stdexcept>
#include <iostream>

#ifdef HAVE_GUROBI
#include "GurobiBackend.h"
#endif

#ifdef HAVE_CPLEX
#include "CplexBackend.h"
#endif

#ifdef HAVE_SCIP
#include "ScipBackend.h"
#endif

std::shared_ptr<LinearSolverBackend>
SolverFactory::createLinearSolverBackend(Preference preference) const {

// by default, create a gurobi backend
#ifdef HAVE_GUROBI

	if (preference == Any || preference == Gurobi)
		try {

			return std::make_shared<GurobiBackend>();

		} catch (const std::exception& e) {

			std::cout << "Could not create Gurobi backend: " << e.what() << std::endl;
		}

#endif

// if this is not available, create a CPLEX backend
#ifdef HAVE_CPLEX

	if (preference == Any || preference == Cplex)
		try {

			return std::make_shared<CplexBackend>();

		} catch (const std::exception& e) {

			std::cout << "Could not create CPLEX backend: " << e.what() << std::endl;
		}

#endif

// if this is not available, create a SCIP backend
#ifdef HAVE_SCIP

	if (preference == Any || preference == Scip)

		try {

			return std::make_shared<ScipBackend>();

		} catch (const std::exception& e) {

			std::cout << "Could not create SCIP backend: " << e.what() << std::endl;
		}

#endif

// if this is not available as well, throw an exception

	throw std::runtime_error("No linear solver available.");
}

std::shared_ptr<QuadraticSolverBackend>
SolverFactory::createQuadraticSolverBackend(Preference preference) const {

// by default, create a gurobi backend
#ifdef HAVE_GUROBI

	if (preference == Any || preference == Gurobi)

		try {

			return std::make_shared<GurobiBackend>();

		} catch (const std::exception& e) {

			std::cout << "Could not create Gurobi backend: " << e.what() << std::endl;
		}

#endif

// if this is not available, create a CPLEX backend
#ifdef HAVE_CPLEX

	if (preference == Any || preference == Cplex)

		try {

			return std::make_shared<CplexBackend>();

		} catch (const std::exception& e) {

			std::cout << "Could not create CPLEX backend: " << e.what() << std::endl;
		}

#endif

// if this is not available, create a SCIP backend
#ifdef HAVE_SCIP

	if (preference == Any || preference == Scip)

		try {

			return std::make_shared<ScipBackend>();

		} catch (const std::exception& e) {

			std::cout << "Could not create SCIP backend: " << e.what() << std::endl;
		}

#endif

// if this is not available as well, throw an exception

	throw std::runtime_error("No quadratic solver available.");
}
