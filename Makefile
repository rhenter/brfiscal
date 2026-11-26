TWINE_REPOSITORY ?= pypi

.PHONY: clean clean-build deps lint format test coverage build check-dist publish release version

clean: clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '__pycache__' -prune -exec rm -rf {} +
	@rm -rf .coverage .pytest_cache .ruff_cache

clean-build:
	@rm -fr build/ dist/ *.egg-info src/*.egg-info

deps:
	uv sync

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff check --fix src tests
	uv run ruff format src tests

test:
	uv run pytest

coverage:
	uv run pytest --cov --cov-report=term-missing

version:
	@uv run python setup.py -q version

build: clean
	uv build

check-dist: build
	uv run twine check dist/*

publish: check-dist
	uv run twine upload --repository $(TWINE_REPOSITORY) dist/*

release: check-dist
	git tag `uv run python setup.py -q version`
	git push origin `uv run python setup.py -q version`
	uv run twine upload --repository $(TWINE_REPOSITORY) dist/*
