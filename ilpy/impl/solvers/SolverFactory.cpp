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
#if defined(_WIN32) || defined(_WIN64)
#define GUROBI_LIB_NAME "ilpy_gurobi.dll"
#define SCIP_LIB_NAME "ilpy_scip.dll"
#elif defined(__APPLE__)
#define GUROBI_LIB_NAME "ilpybackend-gurobi.so"
#define SCIP_LIB_NAME "ilpybackend-scip.so"
#else
#define GUROBI_LIB_NAME "ilpy_gurobi.so"
#define SCIP_LIB_NAME "ilpy_scip.so"
#endif

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

std::shared_ptr<SolverBackend>
SolverFactory::createSolverBackend(Preference preference) const {
  const char *libName = nullptr;

  // Determine which library to load
  if (preference == Gurobi || preference == Any) {
    libName = GUROBI_LIB_NAME;
  } else if (preference == Scip || preference == Any) {
    libName = SCIP_LIB_NAME;
  } else {
    throw std::runtime_error("No solver available.");
  }

  // Load the library
  void *handle = loadLibrary((std::string)libName);
  if (!handle) {
    std::cerr << "Failed to load library: " << libName << " - " << DLERROR()
              << std::endl;
    throw std::runtime_error("Library load failed.");
  }

  // Retrieve the common factory function
  auto createSolverBackend =
      (SolverBackend * (*)()) DLSYM(handle, "createSolverBackend");
  if (!createSolverBackend) {
    std::cerr << "Failed to find symbol 'createSolverBackend' in " << libName
              << " - " << DLERROR() << std::endl;
    DLCLOSE(handle);
    throw std::runtime_error("Symbol lookup failed.");
  }

  try {
    return std::shared_ptr<SolverBackend>(createSolverBackend());
  } catch (const std::exception &e) {
    std::cerr << "Failed to create solver backend: " << e.what() << std::endl;
    DLCLOSE(handle);
    throw;
  }
}