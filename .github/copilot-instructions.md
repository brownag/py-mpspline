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

1. **Input**: Profile dict or list with horizons → `mpspline()` entry point
2. **Validation**: `HorizonSequence` standardizes keys (`top`→`upper`, `bottom`→`lower`) and validates
3. **Processing**: `spline_one()` fits quadratic splines to horizon data
4. **Output**: Returns wide format (dict/DataFrame columns) or long format (DataFrame rows)

### Key Design Decisions

- **Caching in algorithm.py**: `_MATRIX_CACHE` stores spline matrices (Z, R, Q) keyed by `(depths_top, depths_bottom, lam)` to avoid recomputation across profiles—critical for batch processing performance
- **Parallel processing**: `multiprocessing.Pool` in `spline.py` for bulk harmonization with configurable batch size
- **Flexible output**: Three formats: wide (dict), long (DataFrame rows), 1cm (high-resolution)
- **Non-strict validation**: Default behavior skips bad profiles rather than failing—set `strict=True` to raise exceptions

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
make all                # clean → install → lint-fix → test → build
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

**Single profile (returns dict)**:
```python
result = mpspline(profile, output_type='wide')
# → {'cokey': 1234, 'clay_0_5': 22.6, 'clay_5_15': 24.1, ...}
```

**Bulk profiles (returns DataFrame)**:
```python
df = mpspline(profiles_list, output_type='wide')  # Wide: columns per depth
df = mpspline(profiles_list, var_name=['clay'])   # Long: rows per depth (default)
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

When processing many profiles with the **same** `target_depths` and `lam`:
- Matrix computation (Z, R, Q) is cached and subsequent profiles reuse these matrices
- Cache size: max 1000 entries; clears when exceeded
- **Implication**: Batch processing with homogeneous parameters is fast; heterogeneous parameters bust cache

## Testing Patterns

### Fixtures (conftest.py)
- `simple_horizons`: 2-horizon reference data
- `miami_soil`: Full soil component (5 horizons, multiple properties)
- `multiple_components`: 3 component variations for bulk tests
- `invalid_*`: Invalid horizon patterns for error testing

### Test Organization (test_harmonize.py)
```python
class TestHarmonizeComponent:
    def test_simple_component_harmonization(self, simple_horizons):
        # Verify metadata preservation and output structure
    
    def test_custom_target_depths(self, simple_horizons):
        # Verify user-specified depth intervals
    
    def test_invalid_horizons_handling(self):
        # Verify error handling paths
```

**Pattern**: Use fixtures, parameterize with `pytest.mark.parametrize`, assert both data integrity and metadata preservation.

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
2. No schema changes needed—properties are auto-detected from input dicts
3. Add test fixtures with the new property to [conftest.py](conftest.py)

### Extending Output Formats
- Modify `mpspline()` in [spline.py](spline.py#L200)—look for `if output_type == 'wide':`
- Consider impact on single vs. bulk processing paths
- Add tests in [test_harmonize.py](test_harmonize.py) for each output format

### Optimizing Algorithm Performance
- **First check**: Algorithm matrix caching in [algorithm.py](algorithm.py#L42)—is cache effective?
- **Profile parallelization**: Tweak `batch_size` in [spline.py](spline.py#L400)
- **Memory**: Large batches benefit from small `batch_size`; CPU-bound tasks benefit from larger sizes

### Adding Validation Rules
- Extend `validate_horizon_sequence()` in [validation.py](validation.py#L50)
- Return `ValidationResult` with detailed errors/warnings
- Test with fixtures in [conftest.py](conftest.py) under `invalid_*`

## Documentation & References

- **Algorithm**: Bishop et al. (1999) — Modelling soil attribute depth functions with equal-area quadratic smoothing splines
- **Reference R package**: [mpspline2 on CRAN](https://github.com/obrl-soil/mpspline2)
- **Standard depths**: GlobalSoilMap initiative (0-200 cm intervals)
- **Docs**: Built with Sphinx → `make docs` → [docs/_build/html/index.html](docs/_build/html/index.html)

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
