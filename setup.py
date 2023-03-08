import os

from ctypes import util

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

libraries = ["libscip"] if os.name == "nt" else ["scip"]
compile_args = ["-O3", "-std=c++11", "-DHAVE_SCIP"]

# look for various gurobi versions, which are annoyingly
# suffixed with the version number, and wildcards don't work
for v in ["100"]:
    GUROBI_LIB = f"libgurobi{v}" if os.name == 'nt' else f"gurobi{v}"
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
                include_dirs=['ilpy/impl'],
                libraries=libraries,
                language='c++')
        ]),
        extras_require={
          "dev": ["flake8", "pytest", "pytest-cov"],
        },
        package_data={
            "ilpy": ["py.typed", "*.pyi"]
        },
)
