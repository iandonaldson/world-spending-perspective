VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

bootstrap:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install poetry
	$(PYTHON) -m poetry install

venv:
	python3 -m venv $(VENV)

lint:
	$(PYTHON) -m poetry run pytest --disable-warnings

test:
	$(PYTHON) -m poetry run pytest

hello:
	$(PYTHON) src/etl/hello_world.py

coverage:
	$(PYTHON) src/cli.py build-coverage
