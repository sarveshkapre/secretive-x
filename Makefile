VENV ?= .venv
PYTHON_BOOTSTRAP ?= python3
PYTHONPATH := src

# Prefer a local venv when present so `make check` works immediately after `make setup`
# without requiring manual PATH manipulation.
ifeq ($(wildcard $(VENV)/bin/python),)
PYTHON := $(PYTHON_BOOTSTRAP)
PIP := pip
RUFF := ruff
MYPY := mypy
BANDIT := bandit
PIP_AUDIT := pip-audit
else
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
BANDIT := $(VENV)/bin/bandit
PIP_AUDIT := $(VENV)/bin/pip-audit
endif

.PHONY: setup dev test lint typecheck smoke build security check release

setup:
	$(PYTHON_BOOTSTRAP) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements-dev.txt

dev:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m secretive_x.cli --help

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest

lint:
	$(RUFF) check src tests

typecheck:
	$(MYPY) src

smoke:
	@tmp_home="$$(mktemp -d)"; \
	tmp_cfg="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp_home" "$$tmp_cfg"' EXIT; \
	HOME="$$tmp_home" XDG_CONFIG_HOME="$$tmp_cfg" PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m secretive_x.cli init --json >/dev/null; \
	HOME="$$tmp_home" XDG_CONFIG_HOME="$$tmp_cfg" PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m secretive_x.cli version --json >/dev/null; \
	HOME="$$tmp_home" XDG_CONFIG_HOME="$$tmp_cfg" PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m secretive_x.cli info --json >/dev/null; \
	HOME="$$tmp_home" XDG_CONFIG_HOME="$$tmp_cfg" PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m secretive_x.cli list --json >/dev/null

build:
	$(PYTHON) -m build

security:
	$(BANDIT) -q -r src
	$(PIP_AUDIT) -r requirements.txt

check: lint typecheck test smoke security build

release: build
	@echo "Release artifacts are in dist/. Follow docs/RELEASE.md."
