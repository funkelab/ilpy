from __future__ import annotations

import os
from ctypes import util

from Cython.Build import cythonize
from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

# enable test coverage tracing if CYTHON_TRACE is set to a non-zero value
CYTHON_TRACE = int(os.getenv("CYTHON_TRACE") in ("1", "True"))
define_macros = [("CYTHON_TRACE", CYTHON_TRACE)]


include_dirs = ["ilpy/impl"]
library_dirs = []
if os.name == "nt":
    compile_args = ["/O2", "/std:c++17", "/wd4702"]
else:
    compile_args = ["-O3", "-std=c++17", "-Wno-unreachable-code"]


# include conda environment windows include/lib if it exists
# this will be done automatically by conda build, but is useful if someone
# tries to build this directly with pip install in a conda environment
if os.name == "nt" and "CONDA_PREFIX" in os.environ:
    include_dirs.append(os.path.join(os.environ["CONDA_PREFIX"], "Library", "include"))
    library_dirs.append(os.path.join(os.environ["CONDA_PREFIX"], "Library", "lib"))


################ Main wrapper extension ################


wrapper = Extension(
    "ilpy.wrapper",
    sources=["ilpy/wrapper.pyx"],
    extra_compile_args=compile_args,
    include_dirs=include_dirs,
    define_macros=define_macros,
)


ext_modules: list[Extension] = cythonize(
    [wrapper],
    compiler_directives={"linetrace": CYTHON_TRACE, "language_level": "3"},
)


################ Backend extensions ################


BACKEND_SOURCES = [
    "ilpy/impl/solvers/Solution.cpp",
    "ilpy/impl/solvers/Constraint.cpp",
    "ilpy/impl/solvers/Objective.cpp",
]


def _find_lib(lib: str) -> str | None:
    """Platform-independent library search."""
    for prefix in ("lib", ""):
        libname = f"{prefix}{lib}"  # only using gurobi 11 at the moment
        if found := util.find_library(libname):
            print("FOUND library: ", found, libname)
            return libname
    return None


if gurobi_lib := _find_lib("gurobi110"):
    gurobi_backend = Extension(
        name="ilpy.ilpybackend-gurobi",
        sources=["ilpy/impl/solvers/GurobiBackend.cpp", *BACKEND_SOURCES],
        include_dirs=include_dirs,
        libraries=[gurobi_lib],
        library_dirs=library_dirs,
        extra_compile_args=compile_args,
        define_macros=define_macros,
    )
    ext_modules.append(gurobi_backend)
else:
    print("Gurobi library NOT found, skipping Gurobi backend")


if scip_lib := _find_lib("scip"):
    scip_backend = Extension(
        name="ilpy.ilpybackend-scip",
        sources=["ilpy/impl/solvers/ScipBackend.cpp", *BACKEND_SOURCES],
        include_dirs=include_dirs,
        libraries=["scip"],
        library_dirs=library_dirs,
        extra_compile_args=compile_args,
        define_macros=define_macros,
    )
    ext_modules.append(scip_backend)
else:
    print("SCIP library NOT found, skipping SCIP backend")


################ Custom build_ext command ################

# Custom build_ext command to remove platform-specific tags ("cpython-312-darwin")
# from the generated shared libraries.  This makes it easier to discover them


class CustomBuildExt(build_ext):  # type: ignore
    def get_ext_filename(self, fullname: str) -> str:
        filename: str = super().get_ext_filename(fullname)
        if "ilpybackend-" in filename:
            parts = filename.split(".")
            if len(parts) > 2:  # Example: mymodule.cpython-312-darwin.ext
                filename = f"{parts[0]}.{parts[-1]}"
        return filename


setup(ext_modules=ext_modules, cmdclass={"build_ext": CustomBuildExt})
