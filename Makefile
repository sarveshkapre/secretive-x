PYTHON=python3
PYTHONPATH=src

.PHONY: setup dev test lint typecheck smoke build security check release

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
	bandit -q -r src
	pip-audit -r requirements.txt

check: lint typecheck test smoke security build

release: build
	@echo "Release artifacts are in dist/. Follow docs/RELEASE.md."
