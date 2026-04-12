# Copilot Instructions for docat-upload

## Project Overview

**docat-upload** is a Python tool for uploading HTML documentation to a [docat](https://github.com/docat-org/docat) server. It packages documentation folders into ZIP files and uploads them with support for versioning, tagging, and SSL certificate handling.

### Key Features

- Upload HTML documentation to a docat server
- Extract version information from Python modules
- Tag versions (e.g., 'latest')
- Manage documentation versions with pruning
- Support for custom SSL certificates
- Configuration via `.env` file or command-line arguments

---

## Development Workflow

### Environment Setup

This project uses **UV** for Python package management. All Python commands must be run through UV:

```bash
# Initial setup
uv sync
uv run pre-commit install

# Run any Python command
uv run python <script.py>
uv run pytest
uv run mkdocs serve
```

### Quick Commands (Makefile)

Use the Makefile for common development tasks:

```bash
make install      # Set up virtual environment and pre-commit hooks
make check        # Run all code quality checks
make test         # Run tests with coverage
make test-html    # Run tests and open HTML coverage report
make build        # Build wheel distribution
make docs         # Build and serve documentation
make docs-test    # Test documentation build
make help         # Show all available commands
```

---

## Code Quality Tools

### 1. **Ruff** - Linting and Formatting

Configuration in `pyproject.toml`:

- **Target Python**: 3.10+
- **Line length**: 120 characters
- **Auto-fix enabled**: yes

#### Key Rules for Ruff

- **flake8-2020**: Version detection (YTT)
- **flake8-bandit**: Security (S)
- **flake8-bugbear**: Bug detection (B)
- **flake8-builtins**: Builtin shadowing (A)
- **flake8-comprehensions**: Comprehension optimization (C4)
- **isort**: Import sorting (I)
- **pyupgrade**: Syntax modernization (UP)
- **pyflakes**: Logic errors (F)

#### Ignored Rules for Ruff

- E501: Line too long (handled by format)
- E731: Lambda assignment
- S101: Use of assert in tests (allowed in tests/)

#### Ruff usage

```bash
# Run via Makefile (through pre-commit)
make check

# Or manually with UV
uv run ruff check src/
uv run ruff format src/
uv run ruff check --fix src/
```

### 2. **Ty** - Static Type Checking

Configuration in `pyproject.toml`:

- **Python executable**: ./.venv
- **Target version**: Python 3.10

#### Ty usage

```bash
make check  # Includes ty check

# Or manually
uv run ty check
```

### 3. **Pre-commit Hooks**

Automatically runs on every commit:

- Ruff linting and formatting
- Type checking with Ty
- Dependency checking with Deptry

Install with:

```bash
uv run pre-commit install
```

---

## Testing

### Test Configuration

- **Test framework**: pytest
- **Coverage tracking**: pytest-cov
- **Test location**: `tests/`
- **Coverage threshold**: Configured in `pyproject.toml`

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
uv run python -m pytest tests/test_docat_upload.py -v

# Generate HTML coverage report
make test-html

# Run with markers
uv run python -m pytest -k "test_upload" -v
```

### Writing Tests

- Place tests in `tests/` directory
- Use pytest fixtures from `conftest.py`
- Mock external HTTP requests in tests
- Ensure asserts are used (permitted in test files)
- **Test code must pass Ruff and Ty validation**: All test code must comply with the project's linting and type checking rules
  - Run `make check` to validate test code against Ruff rules
  - Run `uv run ty check` to verify type hints in tests
  - Tests follow the same code quality standards as source code
- **Inline ignore comments are acceptable** in tests when dealing with complex testing scenarios:
  - Use `# noqa:` for Ruff and `# ty: ignore` for Ty when necessary
  - Acceptable cases: mocked functions/classes causing type errors, test-specific patterns
  - Always prefer fixing the issue if practical; use inline comments only when the fix is overly complex for testing purposes
  - Include a comment explaining why the ignore is needed

---

## Project Structure

```text
docat-upload/
├── src/docat_upload/
│   ├── __init__.py
│   └── docat_upload.py          # Main module
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   └── test_docat_upload.py     # Test cases
├── docs/                         # MkDocs documentation
├── Makefile                      # Development commands
├── pyproject.toml               # Project configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
└── .github/
    └── copilot-instructions.md  # This file
```

---

## Main Script Functions

### `upload_docs()`

Uploads HTML documentation folder to docat server as a ZIP archive.

- **Parameters**: project, api_key, docs_folder, release, server, verify_ssl
- **Returns**: bool (success/failure)
- **Error handling**: SSL, connection, HTTP errors

### `tag_release()`

Tags an existing documentation version with a label.

- **Parameters**: project, api_key, release, tag, server, verify_ssl
- **Returns**: bool (success/failure)

### `delete_version()`

Deletes a specific documentation version from the server.

- **Parameters**: project, api_key, release, server, verify_ssl
- **Returns**: bool (success/failure)

### `prune_versions()`

Automatically deletes old versions to keep only N most recent.

- **Parameters**: project, api_key, max_versions, server, verify_ssl
- **Returns**: bool (success/failure)

### `get_env()`

Retrieves environment variables from `.env` file or environment.

- **Parameters**: env_key
- **Returns**: str or None

---

## Dependencies

### Core Dependencies

- `requests>=2.33.1` - HTTP client for API calls
- `python-dotenv>=1.2.2` - Environment variable management
- `urllib3>=2.6.3` - HTTP library with SSL support

### Development Dependencies

- `pytest>=9.0.2` - Testing framework
- `pytest-cov>=7.0.0` - Coverage reporting
- `ruff>=0.15.6` - Linting and formatting
- `ty>=0.0.23` - Type checking
- `deptry>=0.24.0` - Dependency linting
- `mkdocs>=1.6.1` - Documentation generation

### Managing Dependencies

```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update lock file
uv lock

# Verify consistency
uv lock --locked
```

---

## Code Style Guidelines

### Formatting

- **Line length**: 120 characters
- **Indentation**: 4 spaces
- **String quotes**: Double quotes (enforced by Ruff)
- **Import order**: isort rules (stdlib → third-party → local)

### Type Hints

- Use modern type hints (Python 3.10+): `str | None` instead of `Optional[str]`
- Add return type annotations to all functions
- Use descriptive parameter names

### Docstrings

- Use NumPy-style docstrings
- Include Parameters, Returns, and Raises sections
- Add type information in docstrings

### Error Handling

- Handle specific exceptions: `SSLError`, `ConnectionError`, `JSONDecodeError`, etc.
- Provide user-friendly error messages
- Use `try-except` blocks strategically

---

## Common Tasks

### Add a New Feature

1. Create feature branch: `git checkout -b feature/feature-name`
2. Write tests first (TDD approach)
3. Implement feature
4. Run `make check` to ensure code quality
5. Run `make test` to verify tests pass
6. Create pull request

### Fix a Bug

1. Write a failing test that reproduces the bug
2. Fix the bug in the code
3. Ensure test passes
4. Run `make check` and `make test`
5. Commit with descriptive message

### Update Documentation

1. Edit `.md` files in `docs/`
2. Run `make docs-test` to verify build
3. Run `make docs` to preview locally
4. Commit changes

### Release a New Version

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run `make check` and `make test`
4. Run `make build-and-publish`
5. Create git tag

---

## Troubleshooting

### UV Command Not Found

- Ensure UV is installed: `pip install uv`
- Use absolute path or add to PATH

### Permission Denied on .venv

```bash
# Recreate virtual environment
rm -rf .venv
uv sync
```

### Ruff Errors Not Auto-fixing

```bash
# Force fix
uv run ruff check --fix src/
uv run ruff format src/
```

### Type Checking Fails

```bash
# Check Ty configuration
uv run ty check --help

# Verify pre-commit is not interfering
uv run pre-commit run --all-files
```

### Test Coverage Low

```bash
# Generate detailed coverage report
make test-html

# Check specific file
uv run python -m pytest --cov=src/docat_upload/docat_upload.py --cov-report=term-missing
```

---

## Resources

- **Project Repository**: <https://github.com/palto42/docat-upload>
- **Documentation**: <https://palto42.github.io/docat-upload/>
- **Docat Server**: <https://github.com/docat-org/docat>
- **UV Documentation**: <https://docs.astral.sh/uv/>
- **Ruff Documentation**: <https://docs.astral.sh/ruff/>
- **Ty Documentation**: <https://docs.astral.sh/ty/>
- **Pytest Documentation**: <https://docs.pytest.org/>

---

## Writing Assistance

When writing code suggestions or tests for this project:

1. **Always use UV** for running Python: `uv run python -m pytest`
2. **Follow Ruff config** (line length 120, modern Python 3.10+ syntax)
3. **Include type hints** using modern syntax (`str | None`)
4. **Add NumPy-style docstrings** with Parameters, Returns, and Raises
5. **Use pytest** with mocking for external dependencies (HTTP requests)
6. **Run `make check`** before suggesting code is ready
7. **Ensure tests pass**: `make test`
8. **Test code must pass Ruff and Ty**: All tests in `tests/` must comply with linting and type checking rules
   - Test files are subject to the same Ruff rules as source code
   - Type hints are required in all test functions and fixtures
   - Run `make check` to validate both source and test code quality
