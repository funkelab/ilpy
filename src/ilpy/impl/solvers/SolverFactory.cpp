#include "SolverFactory.h"
#include "SolverBackend.h"
#include <iostream>
#include <memory>
#include <stdexcept>

// Platform-specific includes andmacros for dynamic library functions
#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#define DLOPEN(lib) LoadLibrary(lib)
#define DLSYM(handle, symbol) GetProcAddress((HMODULE)handle, symbol)
#define DLCLOSE(handle) FreeLibrary((HMODULE)handle)
#define DLERROR() "Failed to load library or symbol (Windows-specific)"
#else
#include <dlfcn.h>
#define DLOPEN(lib) dlopen(lib, RTLD_LAZY)
#define DLSYM(handle, symbol) dlsym(handle, symbol)
#define DLCLOSE(handle) dlclose(handle)
#define DLERROR() dlerror()
#endif

// Platform-specific library names
// These must match the names in setup.py
#if defined(_WIN32) || defined(_WIN64)
#define GUROBI_LIB_NAME "ilpybackend-gurobi.dll"
#define SCIP_LIB_NAME "ilpybackend-scip.dll"
#else
#define GUROBI_LIB_NAME "ilpybackend-gurobi.so"
#define SCIP_LIB_NAME "ilpybackend-scip.so"
#endif

// Free function for loading a backend
std::shared_ptr<SolverBackend> loadBackend(const char *libPath) {
  // Load the library
  void *handle = DLOPEN(libPath);
  if (!handle) {
    throw std::runtime_error(std::string("Failed to load library: ") + libPath +
                             " - " + DLERROR());
  }

  // Retrieve the factory function
  auto createSolverBackend =
      (SolverBackend * (*)()) DLSYM(handle, "createSolverBackend");
  if (!createSolverBackend) {
    DLCLOSE(handle);
    throw std::runtime_error(
        std::string("Failed to find symbol 'createSolverBackend' in ") +
        libPath + " - " + DLERROR());
  }

  // Create the backend
  try {
    return std::shared_ptr<SolverBackend>(createSolverBackend());
  } catch (...) {
    DLCLOSE(handle);
    throw;
  }
}

/**
 * Create a solver backend based on the given preference.
 *
 * @param preference The preferred solver backend. If Any, the first available
 *                  backend will be used.
 *
 * @return A shared pointer to the created solver backend.
 */
std::shared_ptr<SolverBackend>
SolverFactory::createSolverBackend(const std::string &directory,
                                   Preference preference) const {
  std::vector<std::string> libraries;

  // Determine which libraries to try based on preference
  if (preference == Gurobi) {
    libraries.push_back(directory + "/" + GUROBI_LIB_NAME);
  } else if (preference == Scip) {
    libraries.push_back(directory + "/" + SCIP_LIB_NAME);
  } else if (preference == Any) {
    libraries = {directory + "/" + GUROBI_LIB_NAME,
                 directory + "/" + SCIP_LIB_NAME};
  } else {
    throw std::runtime_error("Invalid solver preference.");
  }

  // Attempt to load backends in order
  for (const auto& libPath : libraries) {
    try {
      std::cout << "Trying to load backend from " << libPath << std::endl;
      return loadBackend(libPath.c_str());
    } catch (const std::exception &e) {
      std::cerr << "Warning: Failed to load backend from " << libPath << ": "
                << e.what() << std::endl;
    }
  }

  // If no backends were successfully loaded
  throw std::runtime_error(
      "No suitable solver backend available for preference " +
      preferenceToString(preference));
}
