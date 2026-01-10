# Contributing to mpspline

Thank you for your interest in contributing to mpspline! We welcome contributions from the community. This document provides guidelines and instructions for contributing.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

## Getting Started

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/brownag/mpspline.git
   cd mpspline
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode**:
   ```bash
   make install
   # Or: pip install -e ".[dev,docs]"
   ```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_harmonize.py -v
```

### Code Quality

We use ruff for linting and mypy for type checking.

```bash
# Check for linting issues
make lint

# Auto-fix linting issues and format code
make lint-fix

# Format code only
make format

# Run security checks
make security
```

## Before You Submit

1. **Write tests**: Add tests for any new functionality in the `tests/` directory
2. **Run the test suite**: Ensure all tests pass: `make test`
3. **Check linting**: Run `make lint` and fix any issues
4. **Update documentation**: If adding features, update the README and/or docstrings
5. **Write clear commit messages**: Use present tense ("Add feature" not "Added feature")

## Reporting Bugs

When reporting a bug, please include:
- A clear description of the issue
- Steps to reproduce the problem
- Expected vs. actual behavior
- Python version and OS
- Minimal example code that demonstrates the issue

Create an issue on [GitHub Issues](https://github.com/brownag/mpspline/issues) with this information.

## Suggesting Features

Feature suggestions are welcome! Please create an issue on [GitHub Issues](https://github.com/brownag/mpspline/issues) and include:
- A clear description of the proposed feature
- Why it would be useful
- Example usage if applicable
- Any potential alternatives

## Making Changes

### Code Style

We follow these conventions:
- **Line length**: 100 characters (enforced by ruff)
- **Formatter**: ruff format
- **Linter**: ruff check
- **Type hints**: Use type hints throughout (not required for existing code)
- **Docstrings**: NumPy/Google style docstrings
- **Testing**: pytest framework

### Directory Structure

```
mpspline/
├── src/mpspline/       # Main package source code
│   ├── algorithm.py    # Bishop et al. algorithm implementation
│   ├── spline.py       # Main API functions
│   ├── validation.py   # Input validation
│   ├── constants.py    # Configuration constants
│   └── utils.py        # Utility functions
├── tests/              # Test suite
│   ├── test_validation.py
│   ├── test_harmonize.py
│   ├── test_horizon_sequence.py
│   ├── test_parallel.py
│   └── conftest.py     # Pytest fixtures
├── examples/           # Example scripts
├── docs/               # Sphinx documentation
└── README.md           # Main documentation
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests and documentation as needed
5. Run quality checks:
   ```bash
   make lint
   make test
   make security
   ```
6. Commit with clear messages
7. Push to your fork
8. Create a pull request with a clear description

### Commit Messages

Use clear, descriptive commit messages:
- First line: 50 characters or less, present tense imperative ("Add" not "Added")
- Separate subject from body with blank line
- Wrap body at 72 characters
- Reference related issues: "Fixes #123"

Example:
```
Add parallel processing support for batch harmonization

Implement multiprocessing pool for processing large numbers of
profiles in parallel. Add n_workers parameter to control CPU
utilization. Includes tests and documentation updates.

Fixes #45
```

## Documentation

### Docstrings

All public functions and classes should have docstrings using NumPy/Google style:

```python
def mpspline(
    obj: Union[Dict, List[Dict]],
    var_name: Union[str, List[str]] = None,
) -> Union[Dict, pd.DataFrame]:
    """
    Harmonize soil horizons to standard depths using mass-preserving splines.

    Apply mass-preserving equal-area quadratic spline interpolation to
    convert variable-depth horizon data into fixed-depth intervals.

    Parameters
    ----------
    obj : dict or list of dict
        Single component (dict) or multiple components (list of dicts).
        Each should have a 'horizons' key with horizon data.
    var_name : str or list of str, optional
        Properties to harmonize. If None, processes all numeric properties.

    Returns
    -------
    dict or DataFrame
        Single dict for single profile, DataFrame for multiple profiles.

    Examples
    --------
    >>> result = mpspline({'horizons': [...]})
    >>> df = mpspline([{'horizons': [...]}, ...])
    """
```

### README

Keep the README.md updated with:
- Installation instructions
- Quick start example
- Link to full documentation
- References and citations

### Tests

Write tests that:
- Are clear and focused
- Test one thing at a time
- Use descriptive names: `test_mpspline_single_profile_returns_dict`
- Include docstrings explaining what is tested
- Use pytest fixtures for common test data

Example:
```python
def test_mpspline_single_profile_returns_dict(miami_soil):
    """Test that mpspline() returns dict for single profile input."""
    result = mpspline(miami_soil, var_name=['clay'])
    assert isinstance(result, dict)
    assert 'clay_0_5' in result
```

## Resources

- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Git Book](https://git-scm.com/book)
- [mpspline2 R Package](https://github.com/obrl-soil/mpspline2) - Reference implementation

## Questions?

Feel free to open an issue or discussion on [GitHub](https://github.com/brownag/mpspline) if you have questions or need clarification.

Thank you for contributing! 🙏
