# Makefile (pip + venv workflow)

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PACKAGE := cofogviz
# importable package under src/cofogviz/

.PHONY: bootstrap venv install-dev editable import-check test lint hello coverage clean clean-venv

bootstrap: clean-venv venv install-dev editable import-check
	@echo "Bootstrap complete."

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip wheel

# Install dev deps. Prefer pyproject extras `.[dev]`; fallback to requirements-dev.txt if present
install-dev:
	-$(PYTHON) -m pip install -e ".[dev]" # will install dependencies specified in .dev section of pyproject.toml
	# requirements-dev.txt is optional; if it exists, install from it as well
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi

# Ensure the package itself is installed in editable mode even if no [dev] extra exists
editable:
	$(PYTHON) -m pip install -e .

# Quick import smoke test to catch packaging/path issues early
import-check:
	echo "import importlib; m = importlib.import_module(\"$(PACKAGE)\"); print(m.__name__)" | $(PYTHON)

test:
	PYTHONPATH=src $(PYTHON) -m pytest

lint:
	$(PYTHON) -m pytest --disable-warnings

hello:
	$(PYTHON) src/$(PACKAGE)/etl/hello_world.py

coverage:
	$(PYTHON) src/$(PACKAGE)/cli.py build-coverage

clean-venv:
	@if [ -d "$(VENV)" ]; then \
		echo "Removing existing virtual environment..."; \
		rm -rf $(VENV); \
	fi

clean:
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage dist build \
		.data .cache *.egg-info

