# ilpy

[![License](https://img.shields.io/pypi/l/ilpy.svg)](https://github.com/funkelab/ilpy/raw/main/LICENSE)
[![Anaconda](https://img.shields.io/conda/v/funkelab/ilpy)](https://anaconda.org/funkelab/ilpy)
[![PyPI](https://img.shields.io/pypi/v/ilpy.svg)](https://pypi.org/project/ilpy)
[![CI](https://github.com/funkelab/ilpy/actions/workflows/ci.yaml/badge.svg)](https://github.com/funkelab/ilpy/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/funkelab/ilpy/branch/main/graph/badge.svg)](https://codecov.io/gh/funkelab/ilpy)

Unified python wrappers for popular ILP solvers

**ilpy** is a Python library that provides unified wrappers for popular Integer
Linear Programming (ILP) solvers such as Gurobi and SCIP. It offers a
consistent API that abstracts away the differences between solver
implementations.

With ilpy, you can:

* Define linear and quadratic optimization problems using a simple, intuitive syntax
* Express constraints using natural Python expressions
* Switch between different solver backends (currently Gurobi and SCIP)
* Monitor solver progress through callback events
* Support for continuous, binary, and integer variables

## Installation

Install from pip with:

```bash
pip install ilpy
```

Note that `ilpy` requires a solver backend: either `pyscipopt` (for SCIP) or `gurobipy` (for Gurobi).  

### ... with SCIP

Currently, ilpy ships by default with support for the [SCIP optimization
suite](https://www.scipopt.org), via
[pyscipopt](https://pypi.org/project/PySCIPOpt/), but you may also declare it
explicitly:

```sh
pip install ilpy[scip]
```

### ... with Gurobi

If you want to use Gurobi (which requires a license), you can bring
in the [`gurobipy`](https://pypi.org/project/gurobipy/) dependency with:

```sh
pip install ilpy[gurobi]
```

### On conda

If you prefer to use conda:

#### ...with SCIP

```bash
conda install -c conda-forge ilpy pyscipopt
```

#### ...with Gurobi

```bash
conda install -c conda-forge -c gurobi ilpy gurobi
```

## Local development

```bash
pip install -e .[dev]
pytest
```
