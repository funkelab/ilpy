from ctypes import util

from Cython.Build import cythonize
from setuptools import find_packages, setup
from setuptools.extension import Extension

libraries = ["scip"]
compile_args = ["-O3", "-std=c++11", "-DHAVE_SCIP"]

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
    packages=find_packages(),
    ext_modules=cythonize([
        Extension(
            'ilpy.wrapper',
            sources=['ilpy/wrapper.pyx'],
            extra_compile_args=compile_args,
            include_dirs=['ilpy/impl'],
            libraries=libraries,
            language='c++')
    ]),
    package_data={
        "ilpy": ["py.typed", "*.pyi"]
    },
    extras_require={
        "dev": ["flake8", "pytest", "pytest-cov"],
    },
)
