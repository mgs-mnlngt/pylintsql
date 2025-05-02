# PyLintSQL

A tool that lints/fixes SQL code within Python strings using SQLFluff.

## Installation

```shell
# Install from PyPI
pip install pylintsql
```


## Usage
### Lint SQL in Python files in the current directory
```shell
pylintsql lint
```

### Fix SQL in Python files in a specific directory
```shell
pylintsql fix path/to/directory
```

### Use a custom configuration file
```shell
pylintsql lint --config /path/to/config
```

## SQL String Identification
PyLintSQL identifies SQL strings by looking for the --sql marker at the beginning of the string. Only strings with this marker will be processed:
```python
# This SQL string will be linted
sql = """--sql
    SELECT
      user_id,
      COUNT(*) as order_count
    FROM orders
    WHERE created_at > '2023-01-01'
    GROUP BY user_id
"""

# This regular string will be ignored
other_text = """
    This is not SQL and won't be processed
"""
```

## Configuration
PyLintSQL uses `pyproject.toml` for configuration, which is also a configuration file for SQLFluff itself. This means you can:
* Use all standard SQLFluff configuration options under `[tool.sqlfluff.*]` sections
* Define pylintsql-specific settings under `[tool.pylintsql]`

Example configuration:
```toml
# SQLFluff configuration
[tool.sqlfluff.core]
dialect = "bigquery"  # Or your preferred dialect
max_line_length = 99
exclude_rules = ["RF01", "RF02", "RF04", "ST06"]

[tool.sqlfluff.indentation]
tab_space_size = 2
indented_joins = false
indented_ctes = false

# PyLintSQL specific configuration
[tool.pylintsql]
exclude = [ # Directories/files to exclude
    ".venv/**",  
    "build/**",
    "dist/**",
    "tests/**"
]
```