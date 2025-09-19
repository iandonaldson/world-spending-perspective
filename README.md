# world-spending-perspective
A repository to collect, transform and visualize government spending.

## Troubleshooting

### 1. Rebuilding the Environment
If you encounter issues with the virtual environment (e.g., missing dependencies or corrupted environment), you can rebuild it using the following steps:

1. Remove the existing virtual environment:
   ```bash
   rm -rf .venv
   ```
2. Run the `make bootstrap` command to recreate the environment and install dependencies:
   ```bash
   make bootstrap
   ```

Example errors that indicate a corrupted environment:
- `ModuleNotFoundError: No module named 'duckdb'`
- `bash: .../pip: cannot execute: required file not found`

### 2. Using the `src` Layout
This repository uses the `src` layout for better packaging practices. The installable package is located under `src/cofogviz/`. To install the package in editable mode, run:
```bash
pip install -e .
```

You can then import the package as follows:
```python
import cofogviz
```

### 3. Common Errors and Solutions
- **`ModuleNotFoundError: No module named 'src'`**:
  Ensure you are importing the package name (`cofogviz`) and not `src`.

- **`ModuleNotFoundError: No module named 'tests'`**:
  The `tests/` directory is not a package and does not require an `__init__.py` file.

# Code Organization

This section describes the overall architecture of the project, its components, and their purposes. Each file or directory follows best practices for Python project organization.

## `.github/workflows/ci.yml`
This file defines the Continuous Integration (CI) workflow for the project. It automates tasks such as running tests, linting, and building the project whenever changes are pushed to the repository. CI ensures code quality and prevents regressions.

- **Content**: YAML configuration for GitHub Actions.
- **Example**:
  ```yaml
  name: CI
  on:
    push:
      branches:
        - main
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.12'
        - name: Install dependencies
          run: make bootstrap
        - name: Run tests
          run: make test
  ```
- **Purpose**: Ensures code quality and automates testing.
- **Reference**: [GitHub Actions Documentation](https://docs.github.com/en/actions).

## `.devcontainer/devcontainer.json`
This file configures the development container for Visual Studio Code. It defines the environment, tools, and extensions required for development.

- **Content**: JSON configuration for the development container.
- **Example**:
  ```json
  {
    "name": "Python Dev Container",
    "build": {
      "dockerfile": "Dockerfile"
    },
    "settings": {
      "python.pythonPath": "/usr/local/bin/python3"
    },
    "extensions": ["ms-python.python", "ms-azuretools.vscode-docker"]
  }
  ```
- **Purpose**: Provides a consistent development environment.
- **Reference**: [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers).

## `src/cofogviz` and the `src` Layout
The `src` directory contains the main package (`cofogviz`). Using the `src` layout is a best practice for Python projects as it prevents import issues during testing and development.

- **Content**: Python modules and packages.
- **Example**:
  ```
  src/
  └── cofogviz/
      ├── __init__.py
      ├── routing/
      │   ├── __init__.py
      │   └── choose_source.py
      ├── coverage/
      │   ├── __init__.py
      │   └── build_coverage_registry.py
      └── adapters/
          ├── __init__.py
  ```
- **Purpose**: Organizes the core logic of the project.
- **Reference**: [The `src` Layout](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure).

## `tests`
The `tests` directory contains unit and integration tests for the project. It ensures the correctness of the codebase.

- **Content**: Test files and fixtures.
- **Example**:
  ```
  tests/
  ├── test_routing.py
  └── test_coverage_registry.py
  ```
- **Purpose**: Validates the functionality of the code.
- **Reference**: [Pytest Documentation](https://docs.pytest.org/en/latest/).

## `Makefile`
The `Makefile` defines common tasks for the project, such as setting up the environment, running tests, and cleaning up files.

- **Content**: Task definitions.
- **Example**:
  ```makefile
  bootstrap: clean-venv venv install-dev editable import-check
  	@echo "Bootstrap complete."
  ```
- **Purpose**: Simplifies repetitive tasks.
- **Reference**: [GNU Make Documentation](https://www.gnu.org/software/make/manual/make.html).

## `pyproject.toml`
This file defines the project metadata, dependencies, and build system requirements. It is the modern standard for Python project configuration.

- **Content**: TOML configuration.
- **Example**:
  ```toml
  [build-system]
  requires = ["setuptools", "wheel"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "cofogviz"
  version = "0.1.0"
  dependencies = ["duckdb", "httpx"]

  [project.optional-dependencies]
  dev = ["pytest", "black"]
  ```
- **Purpose**: Manages dependencies and metadata.
- **Reference**: [PEP 518](https://peps.python.org/pep-0518/).

---

This structure ensures the project is well-organized, maintainable, and adheres to modern Python development practices.
