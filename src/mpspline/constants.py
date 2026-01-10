"""
Constants and configuration for mpspline package.

Includes standard depth intervals (GlobalSoilMap), soil properties, and validation thresholds.
"""


# ==============================================================================
# STANDARD DEPTH INTERVALS
# ==============================================================================

# GlobalSoilMap Standard Depths
# These are internationally recognized standard depth intervals used for soil
# property assessment and comparison. Totals to 200 cm, appropriate for most
# temperate to tropical soils.
GLOBALSM_DEPTHS: list[tuple[int, int]] = [
    (0, 5),  # 0-5 cm (topsoil/organic layer interface)
    (5, 15),  # 5-15 cm (topsoil)
    (15, 30),  # 15-30 cm (upper subsoil)
    (30, 60),  # 30-60 cm (mid-subsoil)
    (60, 100),  # 60-100 cm (deep subsoil)
    (100, 200),  # 100-200 cm (very deep/C-horizon)
]

# Alternative depth configurations for other applications
USDA_SOIL_PEDON_DEPTHS: list[tuple[int, int]] = [
    (0, 5),
    (5, 25),
    (25, 50),
    (50, 100),
    (100, 200),
]

SHALLOW_DEPTHS: list[tuple[int, int]] = [
    (0, 5),
    (5, 15),
    (15, 30),
    (30, 50),
]

# ==============================================================================
# STANDARD SOIL PROPERTIES
# ==============================================================================

STANDARD_SOIL_PROPERTIES: dict[str, str] = {
    # Particle size distribution
    "clay": "Clay content (%)",
    "sand": "Sand content (%)",
    "silt": "Silt content (%)",
    # Chemical properties
    "om_r": "Organic matter (%)",
    "ph1to1h2o_r": "pH (1:1 H2O)",
    "ph01mcl_r": "pH (0.01 M CaCl2)",
    "ec_r": "Electrical conductivity (dS/m)",
    "sar_r": "Sodium adsorption ratio",
    "cec7_r": "Cation exchange capacity (meq/100g)",
    "ca_r": "Exchangeable calcium (meq/100g)",
    "mg_r": "Exchangeable magnesium (meq/100g)",
    "k_r": "Exchangeable potassium (meq/100g)",
    "na_r": "Exchangeable sodium (meq/100g)",
    # Physical properties
    "dbthirdbar_r": "Bulk density at 1/3 bar (g/cm3)",
    "awc_r": "Available water capacity (cm/cm)",
    "ksat_r": "Saturated hydraulic conductivity (cm/hr)",
}

# ==============================================================================
# VALIDATION AND ALGORITHM PARAMETERS
# ==============================================================================

# Mass preservation tolerance for spline interpolation
# Allows 0.0001% deviation from original total mass
SPLINE_TOLERANCE: float = 1e-6

# Minimum number of horizons required for spline fitting
MIN_HORIZONS: int = 2

# Maximum depth to consider (cm)
MAX_DEPTH: int = 200

# Depth precision (cm) - minimum depth interval
MIN_DEPTH_INTERVAL: float = 0.1

# ==============================================================================
# HORIZON VALIDATION RULES
# ==============================================================================

# Valid horizon name patterns (simplified)
# These are typical SSURGO horizon designations
VALID_HORIZON_PATTERNS: list[str] = [
    "O",  # Organic (O1, O2, O3, O4)
    "A",  # Surface (A, Ap, A1, A2, A3, A4)
    "B",  # Subsurface (B, BA, B1, B2, B3, Bt, Bh, Bs, etc.)
    "C",  # Parent material (C, Cg, Cr, etc.)
    "R",  # Bedrock (R, Rx)
    "H",  # Not used in SSURGO but included for compatibility
]

# Depth constraints (cm)
DEPTH_CONSTRAINTS = {
    "min_depth_top": 0,  # Top of first horizon should be at or near 0
    "max_horizon_depth": 400,  # Maximum depth for any single horizon
    "min_horizon_thickness": 1,  # Minimum horizon thickness (cm)
}

# ==============================================================================
# LOGGING AND OUTPUT
# ==============================================================================

# Default log level for package
DEFAULT_LOG_LEVEL: str = "INFO"

# Default precision for numeric output
DEFAULT_NUMERIC_PRECISION: int = 2
