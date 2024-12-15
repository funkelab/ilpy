#include "SolverFactory.h"
#include "SolverBackend.h"
#include <Python.h> // For Py_GetPath
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

// Load a library and return a handle
// This function attempts to locate the ilpy.wrapper module and load the library
// from the same directory.
void *loadLibrary(const std::string &libName) {
  // Get the path to the `ilpy.wrapper` module
  PyObject *module = PyImport_ImportModule("ilpy.wrapper");
  if (!module) {
    throw std::runtime_error("Failed to import ilpy.wrapper module");
  }
  PyObject *module_path = PyObject_GetAttrString(module, "__file__");
  if (!module_path) {
    Py_DECREF(module);
    throw std::runtime_error("Failed to get ilpy.wrapper module path");
  }
  std::string path(PyUnicode_AsUTF8(module_path));
  Py_DECREF(module_path);
  Py_DECREF(module);

  // Strip the module filename to get the directory
  auto pos = path.find_last_of('/');
  std::string dir = path.substr(0, pos);

  // Append the library name to the directory
  std::string fullPath = dir + "/" + libName;

  // Load the library
  void *handle = DLOPEN(fullPath.c_str());
  if (!handle) {
    throw std::runtime_error("Failed to load library: " + fullPath + " - " +
                             dlerror());
  }
  return handle;
}

// Free function for loading a backend
std::shared_ptr<SolverBackend> loadBackend(const char *libName) {
  // Load the library
  void *handle = loadLibrary((std::string)libName);
  if (!handle) {
    throw std::runtime_error(std::string("Failed to load library: ") + libName +
                             " - " + DLERROR());
  }

  // Retrieve the factory function
  auto createSolverBackend =
      (SolverBackend * (*)()) DLSYM(handle, "createSolverBackend");
  if (!createSolverBackend) {
    DLCLOSE(handle);
    throw std::runtime_error(
        std::string("Failed to find symbol 'createSolverBackend' in ") +
        libName + " - " + DLERROR());
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
SolverFactory::createSolverBackend(Preference preference) const {
  std::vector<const char *> libraries;

  // Determine which libraries to try based on preference
  if (preference == Gurobi) {
    libraries.push_back(GUROBI_LIB_NAME);
  } else if (preference == Scip) {
    libraries.push_back(SCIP_LIB_NAME);
  } else if (preference == Any) {
    libraries = {GUROBI_LIB_NAME, SCIP_LIB_NAME}; // Specify the order
  } else {
    throw std::runtime_error("Invalid solver preference.");
  }

  // Attempt to load backends in order
  for (const char *libName : libraries) {
    try {
      return loadBackend(libName);
    } catch (const std::exception &e) {
      std::cerr << "Warning: Failed to load backend from " << libName << ": "
                << e.what() << std::endl;
    }
  }

  // If no backends were successfully loaded
  throw std::runtime_error("No suitable solver backend available.");
}