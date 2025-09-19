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
