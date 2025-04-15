# Contributing

ilpy welcomes contributions

## Local development

Clone the repo and install in editable mode.

```bash
git clone <your-fork>
cd ilpy
pip install -e .[dev]
```

### Testing

To run the tests, you can use `pytest`:

```bash
pytest
```

## Deploying

> *This is a note for maintainers*

Create an annotated tag with:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
```

Then push the tag to github:

```bash
git push upstream --follow-tags
```

This will trigger `ci.yaml` to run, which will build a source distribution
(only) and upload it to pypi.
