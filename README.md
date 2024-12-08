# ilpy

[![License](https://img.shields.io/pypi/l/ilpy.svg)](https://github.com/funkelab/ilpy/raw/main/LICENSE)
[![Anaconda](https://img.shields.io/conda/v/funkelab/ilpy)](https://anaconda.org/funkelab/ilpy)
[![PyPI](https://img.shields.io/pypi/v/ilpy.svg)](https://pypi.org/project/ilpy)
[![CI](https://github.com/funkelab/ilpy/actions/workflows/ci.yaml/badge.svg)](https://github.com/funkelab/ilpy/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/funkelab/ilpy/branch/main/graph/badge.svg)](https://codecov.io/gh/funkelab/ilpy)

Unified python wrappers for popular ILP solvers

## Installation

```bash
conda install -c funkelab ilpy
```

## Local development

Clone the repo and install in editable mode.

Note, `ilpy` links against SCIP, so you must have SCIP installed in your environment,
in order to build:

```bash
git clone <your-fork>
cd ilpy

conda create -n ilpy -c conda-forge -c gurobi python scip==9.1.0 gurobi==11.0.3
conda activate ilpy
pip install -e .[dev]
```

If you make local change and want to rebuild the extension quickly, you can run:

```bash
rm -rf build
python setup.py build_ext --inplace
```
