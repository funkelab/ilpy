Steps to build the package
==========================

```bash
# install conda build
conda install conda-build anaconda-client=1.11
conda update conda-build

# then build the recipe
conda build .
# or if you're running this from the root of the repo
conda build conda
```

The last command gives instructions about how to upload the package.
