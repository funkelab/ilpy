import glob
import os
from ctypes import util
from itertools import product

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

print("PATH:", os.environ["PATH"])
print("CONDA_PREFIX:", os.environ.get("CONDA_PREFIX"))


def debug_conda_env() -> None:
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        raise RuntimeError("No active Conda environment found. Ensure Conda is active.")
    print()
    # Check Gurobi DLL directory
    if os.name == "nt":
        bin_dir = os.path.join(conda_prefix, "Library", "bin")
    else:
        bin_dir = os.path.join(conda_prefix, "lib")
    print(f"Inspecting bin directory: {bin_dir}")
    if os.path.exists(bin_dir):
        for file in glob.glob(os.path.join(bin_dir, "*gurobi*")):
            print(f"  Found: {file}")
        for file in glob.glob(os.path.join(bin_dir, "*scip*")):
            print(f"  Found: {file}")
    else:
        print("Gurobi bin directory does not exist!")

    print()
    # Check SCIP include directory
    if os.name == "nt":
        inc_dir = os.path.join(conda_prefix, "Library", "include", "scip")
    else:
        inc_dir = os.path.join(conda_prefix, "include", "scip")
    print(f"Inspecting include directory: {inc_dir}")
    if os.path.exists(inc_dir):
        for file in glob.glob(os.path.join(inc_dir, "*")):
            print(f"  Found: {file}")
    else:
        print("SCIP include directory does not exist!")
    print()


def assert_gurobi_and_scip() -> None:
    # Get the Conda environment prefix
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        raise RuntimeError("CONDA_PREFIX is not set. Ensure Conda is active in CI.")

    # Paths to check
    gurobi_dll_path = os.path.join(conda_prefix, "Library", "bin", "gurobi*.dll")
    scip_header_path = os.path.join(
        conda_prefix, "Library", "include", "scip", "scipdefplugins.h"
    )

    # Verify Gurobi DLL
    gurobi_found = any(os.path.exists(path) for path in glob.glob(gurobi_dll_path))
    if not gurobi_found:
        raise FileNotFoundError(
            f"Gurobi DLL not found in {gurobi_dll_path}. Ensure Gurobi is installed."
        )

    # Verify SCIP header
    if not os.path.exists(scip_header_path):
        raise FileNotFoundError(
            f"SCIP header 'scipdefplugins.h' not found in {scip_header_path}. "
            "Ensure SCIP is installed."
        )

    print("All required files are present.")


debug_conda_env()
if os.name == "nt":
    assert_gurobi_and_scip()

# enable test coverage tracing if CYTHON_TRACE is set to a non-zero value
CYTHON_TRACE = int(os.getenv("CYTHON_TRACE") in ("1", "True"))
if not (CONDA_PREFIX := os.environ.get("CONDA_PREFIX")):
    raise RuntimeError(
        "No active Conda environment found. Activate an environment before running."
    )

libraries = ["libscip"] if os.name == "nt" else ["scip"]
include_dirs = ["ilpy/impl"]
library_dirs = []
if os.name == "nt":
    compile_args = ["/O2", "/DHAVE_SCIP", "/std:c++17", "/wd4702"]
else:
    compile_args = ["-O3", "-DHAVE_SCIP", "-std=c++17", "-Wno-unreachable-code"]

# include conda environment windows include/lib if it exists
# this will be done automatically by conda build, but is useful if someone
# tries to build this directly with pip install in a conda environment
if os.name == "nt":
    include = os.path.join(CONDA_PREFIX, "Library", "include")
    include_dirs.append(include)
    library_dirs.append(os.path.join(CONDA_PREFIX, "Library", "lib"))
    if not os.path.exists(include):
        print(
            "WARNING: Conda include directory not found. "
            "Ensure you have the Conda environment activated."
        )

# look for various gurobi versions, which are annoyingly
# suffixed with the version number, and wildcards don't work


def find_conda_gurobi() -> "tuple[str, str] | tuple[None, None]":
    # Construct the potential library paths
    library_paths = [
        os.path.join(str(CONDA_PREFIX), "Library", "bin"),  # Windows DLLs
        os.path.join(str(CONDA_PREFIX), "lib"),  # macOS/Linux
    ]

    for lib_path in library_paths:
        if os.path.exists(lib_path):
            os.environ["PATH"] += os.pathsep + lib_path  # Dynamically add to PATH

    # Search for Gurobi in the active Conda environment
    for v, prefix in product(range(100, 150, 10), ("lib", "")):
        gurobi_lib = f"{prefix}gurobi{v}"
        if found := util.find_library(gurobi_lib):
            return gurobi_lib, found

    return (None, None)


for v, prefix in product(range(100, 150, 10), ("lib", "")):
    GUROBI_LIB, lib_path = find_conda_gurobi()
    if GUROBI_LIB is not None:
        print(f"FOUND GUROBI library {GUROBI_LIB!r}: {lib_path}")
        libraries.append(GUROBI_LIB)
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
