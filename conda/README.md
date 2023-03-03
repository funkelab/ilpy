Steps to build the package
==========================

```bash
# install conda build
conda install conda-build anaconda-client=1.11
conda update conda-build

# then build the recipe
conda build -c conda-forge -c gurobi .
```

The last command gives instructions about how to upload the package.
