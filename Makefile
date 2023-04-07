default:
	pip install -r requirements.txt
	pip install .
	rm -rf ilpy.egg-info

install-dev:
	pip install -r requirements_dev.txt
	pip install -e .

.PHONY: tests
tests:
	pytest -v --cov=ilpy --cov-report=term-missing
	pre-commit run --all-files

clean:
	rm -rf build dist
	rm -rf ilpy/*.cpp
	rm -rf ilpy/*.so
