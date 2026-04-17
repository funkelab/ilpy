# Contributing

ilpy welcomes contributions

## Local development

This project uses [`uv`](https://docs.astral.sh/uv/) for environment and
dependency management. Clone the repo and sync the dev environment:

```bash
git clone <your-fork>
cd ilpy
uv sync
```

### Testing

To run the tests, use `uv run`:

```bash
uv run pytest
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
