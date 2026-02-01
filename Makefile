PYTHON=python3
PYTHONPATH=src

.PHONY: setup dev test lint typecheck build security check release

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate; pip install -r requirements-dev.txt

dev:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m secretive_x.cli --help

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest

lint:
	ruff check src tests

typecheck:
	mypy src

build:
	$(PYTHON) -m build

security:
	bandit -q -r src
	pip-audit -r requirements.txt

check: lint typecheck test security build

release: build
	@echo "Release artifacts are in dist/. Follow docs/RELEASE.md."
