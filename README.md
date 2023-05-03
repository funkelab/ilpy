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

ilpy links against SCIP, so you must have SCIP installed in your environment.
(You can install via conda)

```bash
conda install scip
```

Then clone the repo and install in editable mode.

```bash
git clone <your-fork>
cd ilpy
pip install -e .[dev]
```
