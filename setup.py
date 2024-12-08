import os
from ctypes import util

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

CONDA_PREFIX = os.environ.get("CONDA_PREFIX")
if CONDA_PREFIX:
    # gurobi seems to be putting its libraries in the top of the conda env
    os.environ["PATH"] += os.pathsep + CONDA_PREFIX
else:
    print("CONDA_PREFIX not set!, did you active a conda environment?")


# enable test coverage tracing if CYTHON_TRACE is set to a non-zero value
CYTHON_TRACE = int(os.getenv("CYTHON_TRACE") in ("1", "True"))

libraries = ["libscip"] if os.name == "nt" else ["scip"]
include_dirs = ["ilpy/impl"]
library_dirs = [CONDA_PREFIX] if CONDA_PREFIX else []
if os.name == "nt":
    compile_args = ["/O2", "/DHAVE_SCIP", "/std:c++17", "/wd4702"]
else:
    compile_args = ["-O3", "-DHAVE_SCIP", "-std=c++17", "-Wno-unreachable-code"]

# include conda environment windows include/lib if it exists
# this will be done automatically by conda build, but is useful if someone
# tries to build this directly with pip install in a conda environment
if os.name == "nt" and "CONDA_PREFIX" in os.environ:
    include_dirs.append(os.path.join(os.environ["CONDA_PREFIX"], "Library", "include"))
    library_dirs.append(os.path.join(os.environ["CONDA_PREFIX"], "Library", "lib"))

# look for various gurobi versions, which are annoyingly
# suffixed with the version number, and wildcards don't work

for prefix in ("lib", ""):
    gurobi_lib = f"{prefix}gurobi110"  # only using gurobi 11 at the moment
    if found := util.find_library(gurobi_lib):
        print("FOUND GUROBI library: ", found)
        libraries.append(gurobi_lib)
        compile_args.append("/DHAVE_GUROBI" if os.name == "nt" else "-DHAVE_GUROBI")
        break
else:
    print("WARNING: GUROBI library not found")


wrapper = Extension(
    "ilpy.wrapper",
    sources=["ilpy/wrapper.pyx"],
    extra_compile_args=compile_args,
    include_dirs=include_dirs,
    libraries=libraries,
    library_dirs=library_dirs,
    language="c++",
    define_macros=[("CYTHON_TRACE", CYTHON_TRACE)],
)

setup(
    ext_modules=cythonize(
        [wrapper],
        compiler_directives={
            "linetrace": CYTHON_TRACE,
            "language_level": "3",
        },
    )
)
