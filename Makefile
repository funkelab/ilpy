.PHONY: default install-dev tests clean build docs

default:
	pip install .

install-dev:
	pip install -e .[dev]

tests:
	pytest -v --cov=ilpy --cov-report=term-missing
	pre-commit run --all-files

clean:
	rm -rf build dist
	rm -rf ilpy/*.cpp
	rm -rf ilpy/*.so

build:
	python setup.py build_ext --inplace

docs:
	cd docs && make html