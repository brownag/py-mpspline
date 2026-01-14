# mpspline: AI Coding Agent Instructions

## Project Overview

**mpspline** is a Python package implementing mass-preserving equal-area quadratic splines for harmonizing soil profiles to standard depth intervals. It's a port of the [mpspline2 R package](https://github.com/obrl-soil/mpspline2) based on [Bishop et al. (1999)](https://doi.org/10.1016/S0016-7061(99)00003-8).

**Core Purpose**: Convert discrete soil property observations at varying depths into standardized depth intervals while preserving mass (integral).

## Architecture

### Module Structure (src/mpspline/)

| Module | Purpose |
|--------|---------|
| `spline.py` | High-level API: `mpspline()` (main entry point), `mpspline_one()`, `HorizonSequence` class, output formatting |
| `algorithm.py` | Low-level math: `spline_one()`, `spline_multiple()` - implements Bishop et al. (1999) algorithm with caching |
| `validation.py` | `ValidationResult`, `validate_horizon_sequence()` - validates input data integrity |
| `constants.py` | `GLOBALSM_DEPTHS` (standard depths), `STANDARD_SOIL_PROPERTIES` dict, validation thresholds |
| `utils.py` | Helper functions for data transformation |

### Data Flow

1. **Input**: Profile dict or list with horizons to `mpspline()` entry point
2. **Validation**: `HorizonSequence` standardizes keys (`top`/`upper`, `bottom`/`lower`) and validates
3. **Processing**: `spline_one()` fits quadratic splines to horizon data
4. **Output**: Returns multiple formats
   - `output_type`: "long" (default, tidy DataFrame format) or "wide" (flat dict/DataFrame columns)
   - `mode`: "dcm" (standard depths, default), "1cm" (1cm resolution), or "icm" (input intervals)

### Key Design Decisions

- **Caching**: `_MATRIX_CACHE` stores spline matrices keyed by (depths_top, depths_bottom, lam) to avoid recomputation
- **Parallel processing**: `multiprocessing.Pool` for bulk harmonization with configurable batch size
- **Flexible output**: Three formats: wide (dict), long (DataFrame rows), 1cm (high-resolution)
- **Non-strict validation**: Skips bad profiles by default; set `strict=True` to raise exceptions

## Development Workflows

### Run Tests
```bash
make test              # Quick run with coverage
make test-cov          # HTML coverage report in htmlcov/
```

### Code Quality
```bash
make lint-fix           # Auto-fix ruff + run mypy
make format             # Format with ruff
```

### Build & Install
```bash
make install            # Dev mode with all extras (dev, spc, docs)
make install-prod       # Production only (core dependencies)
make build              # Package distribution
```

### Documentation
```bash
make docs               # Build Sphinx HTML in docs/_build/html/
```

### Full Pipeline
```bash
make all                # clean, install, lint-fix, test, build
```

## Critical Patterns

### Input Data Structure
```python
{
    'cokey': 1234,                    # Metadata (optional, preserved in output)
    'compname': 'Miami',
    'horizons': [
        {
            'hzname': 'Ap',           # Horizon name (optional)
            'upper': 0,               # Depth to top (cm) - required
            'lower': 20,              # Depth to bottom (cm) - required
            'clay': 24.5,             # Properties (numeric, required)
            'sand': 42.3,
        },
        {'hzname': 'Bt', 'upper': 20, 'lower': 50, 'clay': 35.2, 'sand': 28.1}
    ]
}
```

**Key Points**:
- Depth aliases: accepts `top`/`bottom` OR `upper`/`lower` (standardized internally)
- Properties are auto-detected numeric fields (no explicit schema needed)
- Horizons must be **sequential** (no gaps, no overlaps)

### Entry Point Patterns

**Single profile with long format (returns list of dicts)**:
```python
result = mpspline_one(profile, output_type='long')
# [{'cokey': 1234, 'var_name': 'clay', 'upper': 0, 'lower': 5, 'value': 22.6}, ...]
```

**Single profile with wide format (returns dict)**:
```python
result = mpspline_one(profile, output_type='wide', mode='dcm')
# {'cokey': 1234, 'clay_0_5': 22.6, 'clay_5_15': 24.1, ...}
```

**Single profile with wide format (input intervals)**:
```python
result = mpspline_one(profile, output_type='wide', mode='icm')
# {'cokey': 1234, 'clay_0_20': 28.0, 'clay_20_50': 35.2, ...}
```

**Bulk profiles with long format (default, returns DataFrame)**:
```python
df = mpspline(profiles_list)  # Long format (tidy data)
# Columns: [cokey, var_name, upper, lower, value]
```

**Bulk profiles with wide format (returns DataFrame)**:
```python
df = mpspline(profiles_list, output_type='wide')  # Wide format (spreadsheet-style)
# Columns: [cokey, clay_0_5, clay_5_15, sand_0_5, ...]
```

**High-resolution 1cm output**:
```python
df = mpspline(profiles_list, mode='1cm')  # Depth every 1cm
# Long format: [cokey, var_name, depth, value]
df = mpspline(profiles_list, output_type='wide', mode='1cm')  # 1cm columns
# Wide format: [cokey, clay_0cm, clay_1cm, clay_2cm, ...]
```

**Input interval mode (original horizon depths)**:
```python
df = mpspline(profiles_list, mode='icm')  # Use original horizon depth intervals
# Long: [cokey, var_name, upper, lower, value]
# Wide: [cokey, clay_0_20, clay_20_50, ...] (original depths as columns)
```

**Custom depths**:
```python
result = mpspline(profile, target_depths=[(0, 10), (10, 30), (30, 50)])
```

**Parallel processing**:
```python
df = mpspline(profiles_list, parallel=True, batch_size=500)  # Use multiprocessing
```

### Validation & Error Handling

- **Non-strict** (default): Skips profiles with errors, logs warnings
  ```python
  df = mpspline(profiles, strict=False)  # Bad profiles silently skipped
  ```
- **Strict mode**: Raises exceptions on validation failure
  ```python
  try:
      df = mpspline(profiles, strict=True)
  except ValueError as e:
      print(f"Validation error: {e}")
  ```

**Common validation errors**:
- Gaps in depth coverage (e.g., 0-20, then 30-50)
- Overlapping horizons
- Inverted depths (`upper > lower`)
- Missing required fields (`upper`, `lower`)
- Non-sequential horizons

### Algorithm Caching

When processing many profiles with same `target_depths` and `lam`:
- Matrix computation is cached; subsequent profiles reuse matrices
- Cache limit: 1000 entries
- Homogeneous batches are fast; heterogeneous parameters bust cache

## Testing Patterns

### Fixtures (conftest.py)
- `simple_horizons`: 2-horizon reference data (clay, sand, silt, om_r properties)
- `miami_soil`: Full soil component (5 horizons, multiple properties)
- `multiple_components`: 3 component variations for bulk tests
- `invalid_*`: Invalid horizon patterns for error testing

### Test Organization (test_harmonize.py)

Use dedicated test classes for different aspects:
```python
class TestHarmonizeComponent:
    """Test mpspline_one() with long format (default)"""
    
class TestWideFormat:
    """Test wide format output (backward compatibility)"""
    
class TestHarmonizeComponentsBulk:
    """Test mpspline() for multiple profiles"""
    
class TestModes:
    """Test output modes: dcm, 1cm, icm"""
```

**Test Utilities**: Use `extract_numeric_properties()` from [utils.py](utils.py) to avoid duplicating property detection logic in tests.

**Pattern**: Use fixtures, validate both data integrity and metadata preservation, use dynamic assertions (avoid hardcoding expected row counts).

## Configuration & Constants

**Key files**:
- `constants.py`: `GLOBALSM_DEPTHS` (default: 0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm)
- `pyproject.toml`: Python 3.10+, dependencies: numpy, pandas, scipy (core)
- `Makefile`: All development commands

**Important constants**:
- `SPLINE_TOLERANCE = 1e-6`: Mass preservation tolerance
- `MIN_HORIZONS = 2`: Minimum for spline fitting
- `MAX_CACHE_SIZE = 1000`: Algorithm matrix cache limit

## Common AI Agent Tasks

### Adding a New Property
1. If it's a standard soil property, add to `STANDARD_SOIL_PROPERTIES` dict in [constants.py](constants.py)
2. No schema changes needed. Properties are auto-detected from input dicts
3. Add test fixtures with the new property to [conftest.py](conftest.py)

### Extending Output Formats
- Modify `mpspline_one()` in [spline.py](spline.py#L220) for single-profile logic
- Modify `mpspline()` in [spline.py](spline.py#L380) for bulk processing
- Update output_type and mode handling for all paths
- Add tests in [test_harmonize.py](test_harmonize.py) for new combinations

### Optimizing Algorithm Performance
- **First check**: Algorithm matrix caching in [algorithm.py](algorithm.py#L42). Is cache effective?
- **Profile parallelization**: Tweak `batch_size` in [spline.py](spline.py#L400)
- **Memory**: Large batches benefit from small `batch_size`; CPU-bound tasks benefit from larger sizes

### Adding Validation Rules
- Extend `validate_horizon_sequence()` in [validation.py](validation.py#L50)
- Return `ValidationResult` with detailed errors/warnings
- Test with fixtures in [conftest.py](conftest.py) under `invalid_*`

## Documentation & References

- **Algorithm**: Bishop et al. (1999) - Modelling soil attribute depth functions with equal-area quadratic smoothing splines
- **Reference R package**: [mpspline2 on CRAN](https://github.com/obrl-soil/mpspline2)
- **Standard depths**: GlobalSoilMap initiative (0-200 cm intervals)
- **Docs**: Built with Sphinx: `make docs` produces [docs/_build/html/index.html](docs/_build/html/index.html)

## Type Hints & Code Style

- **Target**: Python 3.10+
- **Style**: Black (100 char line length), ruff linting, mypy type checking
- **Patterns**:
  - Use `list[dict]` not `List[Dict]` (Python 3.10+ syntax)
  - Dataclasses for structured returns (`ValidationResult`)
  - Type hints on function signatures (not enforced via mypy but encouraged)
  - Docstrings: Module-level, class-level, and complex function-level

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make test` | Run tests with coverage |
| `make lint-fix` | Auto-fix linting issues |
| `make install` | Dev setup |
| `make all` | Full pipeline |
| `pytest tests/test_harmonize.py::TestHarmonizeComponent::test_simple_component_harmonization` | Run single test |
