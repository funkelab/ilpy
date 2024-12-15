import os

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

# enable test coverage tracing if CYTHON_TRACE is set to a non-zero value
CYTHON_TRACE = int(os.getenv("CYTHON_TRACE") in ("1", "True"))
define_macros = [("CYTHON_TRACE", CYTHON_TRACE)]
include_dirs = ["ilpy/impl"]
if os.name == "nt":
    compile_args = ["/O2", "/std:c++17", "/wd4702"]
else:
    compile_args = ["-O3", "-std=c++17", "-Wno-unreachable-code"]


BACKEND_SOURCES = [
    "ilpy/impl/solvers/Solution.cpp",
    "ilpy/impl/solvers/Constraint.cpp",
    "ilpy/impl/solvers/Objective.cpp",
]

# Define the wrapper library for GurobiBackend
gurobi_backend = Extension(
    name="ilpy.ilpy_gurobi",  # This name is used for the resulting library
    sources=["ilpy/impl/solvers/GurobiBackend.cpp", *BACKEND_SOURCES],
    include_dirs=["ilpy/impl"],  # Include directories for headers
    libraries=["gurobi110"],  # Link against Gurobi
    extra_compile_args=compile_args,
    define_macros=define_macros,
)

# Define the wrapper library for ScipBackend
scip_backend = Extension(
    name="ilpy.ilpy_scip",  # This name is used for the resulting library
    sources=["ilpy/impl/solvers/ScipBackend.cpp", *BACKEND_SOURCES],
    include_dirs=["ilpy/impl"],  # Include directories for headers
    libraries=["scip"],  # Link against scip
    extra_compile_args=compile_args,
    define_macros=define_macros,
)


wrapper = Extension(
    "ilpy.wrapper",
    sources=["ilpy/wrapper.pyx"],
    extra_compile_args=compile_args,
    include_dirs=["ilpy/impl"],
    define_macros=define_macros,
)

setup(
    ext_modules=[
        *cythonize(
            [wrapper],
            compiler_directives={
                "linetrace": CYTHON_TRACE,
                "language_level": "3",
            },
        ),
        gurobi_backend,
        scip_backend,
    ],
)
