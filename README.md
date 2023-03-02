# ilpy

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
