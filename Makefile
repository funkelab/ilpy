default:
	pip install -r requirements.txt
	pip install .
	rm -rf ilpy.egg-info

install-dev:
	pip install -r requirements_dev.txt
	pip install -e .

.PHONY: tests
tests:
	pytest -v --cov=ilpy -s ilpy
	flake8 ilpy
