"""
Validation utilities for horizon sequences and component data.

Provides validation functions for checking horizon sequence integrity,
data types, and reasonable value ranges before spline processing.
"""

import logging
from dataclasses import dataclass, field

import numpy as np

from .constants import (
    DEPTH_CONSTRAINTS,
    MAX_DEPTH,
    MIN_HORIZONS,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of horizon sequence validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    horizon_count: int = 0
    max_depth: int = 0

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid

    def __str__(self) -> str:
        """String representation of validation result."""
        status = "✓ Valid" if self.is_valid else "✗ Invalid"
        msg = f"{status} ({self.horizon_count} horizons, depth {self.max_depth} cm)"

        if self.warnings:
            msg += f"\nWarnings: {'; '.join(self.warnings)}"

        if self.errors:
            msg += f"\nErrors: {'; '.join(self.errors)}"

        return msg


def validate_horizon_sequence(
    horizons: list[dict],
    strict: bool = False,
) -> ValidationResult:
    """
    Validate a sequence of horizons for spline processing.

    Checks:
    - Minimum number of horizons present
    - Required fields present in each horizon
    - Sequential/continuous depths (no gaps or major overlaps)
    - Numeric types and reasonable ranges
    - Depth consistency

    Args:
        horizons: List of horizon dicts with keys:
            - hzname: Horizon name (str)
            - upper: Depth to top (cm, int/float)
            - lower: Depth to bottom (cm, int/float)
            - [property names]: Property values (float)
        strict: If True, be more restrictive about gaps and ranges

    Returns:
        ValidationResult with is_valid flag and detailed error/warning messages
    """
    result = ValidationResult(is_valid=True)

    if not horizons:
        result.is_valid = False
        result.errors.append("No horizons provided")
        return result

    if len(horizons) < MIN_HORIZONS:
        result.is_valid = False
        result.errors.append(
            f"Insufficient horizons: {len(horizons)} provided, minimum {MIN_HORIZONS} required"
        )
        return result

    result.horizon_count = len(horizons)

    # Check required fields and types
    for i, hz in enumerate(horizons):
        hz_name = hz.get("hzname", f"Horizon {i}")

        # Check required fields
        required_fields = ["hzname", "upper", "lower"]
        missing_fields = [f for f in required_fields if f not in hz]
        if missing_fields:
            result.is_valid = False
            result.errors.append(
                f"Horizon '{hz_name}' (index {i}) missing fields: {', '.join(missing_fields)}"
            )
            continue

        # Check numeric types
        try:
            depth_top = float(hz["upper"])
            depth_bottom = float(hz["lower"])
        except (TypeError, ValueError, KeyError) as e:
            result.is_valid = False
            if isinstance(e, KeyError):
                result.errors.append(f"Horizon '{hz_name}' (index {i}) missing field: {e}")
            else:
                result.errors.append(
                    f"Horizon '{hz_name}' (index {i}) has non-numeric depths: "
                    f"upper={hz.get('upper')}, lower={hz.get('lower')}"
                )
            continue

        # Check depth logic
        if depth_top < DEPTH_CONSTRAINTS["min_depth_top"]:
            result.is_valid = False
            result.errors.append(
                f"Horizon '{hz_name}' (index {i}) has negative depth top: {depth_top} cm"
            )

        if depth_bottom <= depth_top:
            result.is_valid = False
            result.errors.append(
                f"Horizon '{hz_name}' (index {i}) depth inverted or equal: "
                f"{depth_top}-{depth_bottom} cm"
            )

        thickness = depth_bottom - depth_top
        min_thickness = DEPTH_CONSTRAINTS.get("min_horizon_thickness", 1)
        if thickness < min_thickness:
            result.warnings.append(f"Horizon '{hz_name}' (index {i}) very thin: {thickness} cm")

        if depth_bottom > DEPTH_CONSTRAINTS["max_horizon_depth"]:
            if strict:
                result.errors.append(
                    f"Horizon '{hz_name}' (index {i}) exceeds max depth: {depth_bottom} cm"
                )
            else:
                result.warnings.append(
                    f"Horizon '{hz_name}' (index {i}) exceeds typical depth: {depth_bottom} cm"
                )

        # Check property values
        numeric_properties = {
            k: v
            for k, v in hz.items()
            if k not in {"hzname", "upper", "lower"} and isinstance(v, (int, float, str))
        }

        for prop_name, prop_value in numeric_properties.items():
            if isinstance(prop_value, str):
                try:
                    float(prop_value)
                except ValueError:
                    result.warnings.append(
                        f"Horizon '{hz_name}' property '{prop_name}' is string: '{prop_value}'"
                    )
            elif isinstance(prop_value, (int, float)):
                # Check for NaN/Inf
                if isinstance(prop_value, float) and (np.isnan(prop_value) or np.isinf(prop_value)):
                    result.warnings.append(
                        f"Horizon '{hz_name}' property '{prop_name}' is {prop_value}"
                    )

    # Check sequence continuity and overlaps (only if all horizons are valid)
    if len(horizons) > 1 and result.is_valid:
        sorted_hz = sorted(horizons, key=lambda h: float(h["upper"]))

        for i in range(len(sorted_hz) - 1):
            hz1 = sorted_hz[i]
            hz2 = sorted_hz[i + 1]

            depth1_bottom = float(hz1["lower"])
            depth2_top = float(hz2["upper"])

            gap = depth2_top - depth1_bottom
            if gap > 0:
                result.warnings.append(
                    f"Gap detected between horizons: {hz1['hzname']} (bottom {depth1_bottom} cm) "
                    f"and {hz2['hzname']} (top {depth2_top} cm), gap = {gap} cm"
                )

            if gap < 0:  # Overlap
                result.warnings.append(
                    f"Overlap detected between horizons: {hz1['hzname']} ({depth1_bottom} cm) "
                    f"and {hz2['hzname']} ({depth2_top} cm), overlap = {abs(gap)} cm"
                )

    # Set max depth
    if horizons:
        max_depth = max(float(h["lower"]) for h in horizons)
        result.max_depth = int(max_depth)

        if result.max_depth > MAX_DEPTH:
            result.warnings.append(
                f"Maximum depth {result.max_depth} cm exceeds typical {MAX_DEPTH} cm"
            )

    return result


def validate_mass_preservation(
    original_mass: float,
    splined_mass: float,
    tolerance: float = 1e-6,
) -> bool:
    """
    Check that spline preserves total mass within tolerance.

    Args:
        original_mass: Total mass from original horizons
        splined_mass: Total mass from splined predictions
        tolerance: Relative tolerance (default 0.0001%)

    Returns:
        True if mass is preserved within tolerance, False otherwise
    """
    if original_mass == 0:
        return splined_mass == 0

    relative_error = abs(splined_mass - original_mass) / abs(original_mass)
    return relative_error <= tolerance
