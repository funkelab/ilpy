import os

from ctypes import util

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

libraries = ["scip"]
library_dirs = []
include_dirs = ['ilpy/impl']
compile_args = ["-O3", "-std=c++11", "-DHAVE_SCIP"]

# include conda environment windows include/lib if it exists
# this will be done automatically by conda build, but is useful if someone
# tries to build this directly with pip install in a conda environment
if 'CONDA_PREFIX' in os.environ:
    win_include = os.path.join(os.environ['CONDA_PREFIX'], 'Library', 'include')
    if os.path.exists(win_include):
        include_dirs.append(win_include)
    win_lib = os.path.join(os.environ['CONDA_PREFIX'], 'Library', 'bin')
    if os.path.exists(win_lib):
        library_dirs.append(win_lib)
    

# look for various gurobi versions, which are annoyingly
# suffixed with the version number, and wildcards don't work
for v in ["100"]:
    GUROBI_LIB = f"gurobi{v}"
    if (gurolib := util.find_library(GUROBI_LIB)) is not None:
        print("FOUND GUROBI library: ", gurolib)
        libraries.append(GUROBI_LIB)
        compile_args.append("-DHAVE_GUROBI")
        break
else:
    print("WARNING: GUROBI library not found")


setup(
        name='ilpy',
        version='0.2',
        description='Python wrappers for popular MIP solvers.',
        url='https://github.com/funkelab/ilpy',
        author='Jan Funke',
        author_email='funkej@janelia.hhmi.org',
        license='MIT',
        packages=[
            'ilpy'
        ],
        ext_modules=cythonize([
            Extension(
                'ilpy.wrapper',
                sources=[
                    'ilpy/wrapper.pyx',
                ],
                extra_compile_args=compile_args,
                include_dirs=include_dirs,
                libraries=libraries,
                library_dirs=library_dirs,
                language='c++')
        ]),
        extras_require={
          "dev": ["flake8", "pytest", "pytest-cov"],
        },
        package_data={
            "ilpy": ["py.typed", "*.pyi"]
        },
)
