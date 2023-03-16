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

### Deploying

> Only for maintainers

Bump the version in `__init__.py` and commit it.

Then create an annotated tag with:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
```

Then push the tag to github:

```bash
git push upstream --follow-tags
```

This will trigger `ci.yaml` to run, which will build a source distribution
(only) and upload it to pypi.

Once that is done, to deploy to anaconda, open a PR to https://github.com/funkelab/ilpy-feedstock
that update the version and SHA256 hash in `meta.yaml`.
(You can find the hash in the files page of the appropriate version release on
pypi... for example https://pypi.org/project/ilpy/0.2.2/#files)

```yaml
# ...
{% set version = "<UPDATE VERSION HERE>" %}

source:
  # ...
  sha256: <INSERT VERSION-SPECIFIC PYPI SHA HERE>
```

Once the PR is merged, github actions will run and push the conda packages for each platform to anaconda.
