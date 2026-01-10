"""
mpspline: Mass-preserving equal-area quadratic splines for soil profile depth harmonization

This package provides Python implementation of mass-preserving equal-area quadratic splines
based on the mpspline2 R package (Malone et al., 2009).

Reference:
    Malone, B. P., McBratney, A. B., & Minasny, B. (2009). Mapping continuous depth functions
    of soil carbon storage and available water capacity. Geoderma, 154(3-4), 138-152.

See Also:
    - mpspline2 (R package): https://github.com/obrl-soil/mpspline2
    - GlobalSoilMap: https://www.globalsoilmap.org/

Basic Usage:
    >>> from mpspline import mpspline
    >>>
    >>> # Single component harmonization
    >>> component = {
    ...     'cokey': 1234,
    ...     'compname': 'Miami',
    ...     'horizons': [
    ...         {'hzname': 'Ap', 'upper': 0, 'lower': 20, 'clay': 24.5},
    ...         {'hzname': 'Bt', 'upper': 20, 'lower': 50, 'clay': 35.2},
    ...     ]
    ... }
    >>> result = mpspline(component)
    >>> print(result['clay_0_5'])
    21.4
"""

from .__version__ import __version__
from .algorithm import (
    spline_multiple,
    spline_one,
)
from .constants import GLOBALSM_DEPTHS, SPLINE_TOLERANCE, STANDARD_SOIL_PROPERTIES
from .spline import (
    HorizonSequence,
    mpspline,
    mpspline_one,
    to_soilprofilecollection,
)
from .validation import ValidationResult, validate_horizon_sequence

__all__ = [
    # Version
    "__version__",
    # Constants
    "GLOBALSM_DEPTHS",
    "STANDARD_SOIL_PROPERTIES",
    "SPLINE_TOLERANCE",
    # Core classes and functions
    "HorizonSequence",
    "mpspline_one",
    "mpspline",
    "to_soilprofilecollection",
    # Algorithm (Bishop et al. 1999)
    "spline_one",
    "spline_multiple",
    # Validation
    "validate_horizon_sequence",
    "ValidationResult",
]
