# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-13

This release introduces flexible output formats and modes, allowing users to choose between tidy (long) and spreadsheet-style (wide) formats, with support for multiple depth resolution modes.

### New Output Formats

- **Long Format (Default)**: Returns tidy data structure with one record per depth-property combination, ideal for data analysis and visualization workflows
- **Wide Format**: Returns spreadsheet-style output with flattened columns (e.g., clay_0_5, clay_5_15), maintaining backward compatibility and suited for tabular analysis
- Consistent output types across single and bulk profile processing

### Output Modes

- **DCM Mode (Default)**: Standard GlobalSoilMap depth intervals (0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm)
- **1CM Mode**: High-resolution output at every 1 centimeter increment for detailed depth analysis
- **ICM Mode**: Preserves original input component horizon depth intervals while applying spline harmonization

### API Enhancements

- Added output_type parameter to mpspline() and mpspline_one() - specify "long" (default) or "wide"
- Added mode parameter to control depth resolution - "dcm" (default), "1cm", or "icm"
- Improved error handling with consistent return types based on output format
- Enhanced documentation with detailed examples for each format and mode combination

### Testing & Quality

- Refactored test suite to validate new default long format behavior
- Added comprehensive tests for wide format and all output modes
- Dynamic property detection in tests to avoid hardcoded fixture dependencies
- More precise assertions replacing approximate calculations

### Documentation Updates

- Updated README.md with clear examples of long and wide formats
- Enhanced API documentation with detailed parameter descriptions
- Added usage examples for all output modes (dcm, 1cm, icm)
- Improved troubleshooting guide and parameter reference
- Comprehensive AI coding agent instructions in `.github/copilot-instructions.md` with architecture guidance, critical patterns, and development workflows
- Critical Guidelines section documenting git & version control rules (no remote pushes, commits require approval, ASCII-only content)

### Code Quality Improvements

- Extracted `extract_numeric_properties()` utility function to reduce code duplication
- Improved float depth handling with `int(round())` for proper rounding
- Removed all unicode characters (arrows, em-dashes, emoji) from documentation for ASCII-only compliance

## [0.1.0] - 2025-01-11

### Added
- Initial release
- Mass-preserving equal-area quadratic spline implementation (Bishop et al., 1999)
- Support for single profile harmonization: pass a dict, get harmonized dict
- Support for batch profile processing: pass list of dicts, get pandas DataFrame
- Optional parallel processing for large datasets using multiprocessing
- Customizable depth intervals (default: GlobalSoilMap standard)
- Tunable smoothing parameter (lambda) for controlling fit
- Value constraints (vlow, vhigh) for enforcing realistic ranges
- Comprehensive input validation with strict/lenient modes
- Automatic horizon depth field recognition (multiple naming conventions)
- Flexible property detection (any numeric field can be harmonized)
- Comprehensive docstrings with NumPy style documentation
- Full type hints throughout codebase
- Extensive test suite (4 test files, 808 lines of tests)
- Example scripts demonstrating basic usage, batch processing, custom depths, and parameter tuning
- Documentation with parameter guidance, troubleshooting, and FAQ

### Features
- **Data-agnostic**: Works with dictionaries, lists, or pandas DataFrames
- **Flexible input**: Automatically recognizes common horizon depth column names (upper/lower, top/bottom, hzdept_r/hzdepb_r, etc.)
- **Mass-preserving**: Maintains average property values across depth intervals
- **Bulk processing**: Efficiently handle hundreds or thousands of soil profiles
- **Parallel processing**: Optional multiprocessing for large datasets
- **Customizable**: Adjust smoothing parameters, depth intervals, and value constraints
- **Robust validation**: Comprehensive error handling with detailed validation messages
- **Well-documented**: Full docstrings and extensive type hints

### Technical Details
- Python 3.10+ support
- Dependencies: numpy >= 1.20.0, pandas >= 1.3.0, scipy >= 1.7.0
- Port of mpspline2 R package (Lauren O'Brien)
- Based on Bishop et al. (1999) and Malone et al. (2009) research

### References
- Bishop, T.F.A., McBratney, A.B., & Laslett, G.M. (1999). Modelling soil attribute depth functions with equal-area quadratic smoothing splines. *Geoderma*, 89(3-4), 185-208. https://doi.org/10.1016/S0016-7061(99)00003-8
- Malone, B.P., McBratney, A.B., & Minasny, B. (2009). Mapping continuous depth functions of soil carbon storage and available water capacity. *Geoderma*, 154(3-4), 138-152. https://doi.org/10.1016/j.geoderma.2009.10.007
- O'Brien, L. (2025). mpspline2: Mass-Preserving Spline Functions for Soil Data. R package version 0.1.9. https://github.com/obrl-soil/mpspline2

[0.1.0]: https://github.com/brownag/mpspline/releases/tag/v0.1.0
