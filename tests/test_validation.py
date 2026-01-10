"""
Tests for validation module.

Tests ValidationResult, validate_horizon_sequence, and mass preservation checks.
"""

import numpy as np

from mpspline.validation import (
    ValidationResult,
    validate_horizon_sequence,
    validate_mass_preservation,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True, horizon_count=5, max_depth=120)

        assert result.is_valid
        assert result.horizon_count == 5
        assert result.max_depth == 120
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert bool(result) is True

    def test_invalid_result(self):
        """Test creating an invalid result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Missing upper"],
            horizon_count=0,
        )

        assert not result.is_valid
        assert bool(result) is False
        assert "Missing upper" in result.errors

    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = ValidationResult(
            is_valid=True,
            warnings=["Gap detected"],
            horizon_count=2,
        )

        assert result.is_valid
        assert "Gap detected" in result.warnings

    def test_str_representation(self):
        """Test string representation."""
        result = ValidationResult(is_valid=True, horizon_count=5, max_depth=120)
        str_repr = str(result)

        assert "Valid" in str_repr
        assert "5" in str_repr
        assert "120" in str_repr


class TestValidateHorizonSequence:
    """Test validate_horizon_sequence function."""

    def test_valid_simple_horizons(self, simple_horizons):
        """Test validation of simple valid horizons."""
        result = validate_horizon_sequence(simple_horizons)

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.horizon_count == 2

    def test_valid_miami_soil(self, miami_soil):
        """Test validation of Miami soil component."""
        result = validate_horizon_sequence(miami_soil["horizons"])

        assert result.is_valid
        assert result.horizon_count == 5
        assert result.max_depth == 120

    def test_empty_horizons(self):
        """Test validation of empty horizon list."""
        result = validate_horizon_sequence([])

        assert not result.is_valid
        assert "No horizons provided" in result.errors

    def test_insufficient_horizons(self, horizon_single):
        """Test validation with insufficient horizons."""
        result = validate_horizon_sequence(horizon_single)

        assert not result.is_valid
        assert "Insufficient horizons" in result.errors[0]

    def test_missing_required_fields(self):
        """Test validation of horizons missing required fields."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20},
            {"hzname": "Bt", "lower": 50},  # Missing upper
        ]

        result = validate_horizon_sequence(horizons)

        assert not result.is_valid
        assert any("missing fields" in err.lower() for err in result.errors)

    def test_non_numeric_depths(self):
        """Test validation with non-numeric depths."""
        horizons = [
            {"hzname": "Ap", "upper": "zero", "lower": 20},
            {"hzname": "Bt", "upper": 20, "lower": 50},
        ]

        result = validate_horizon_sequence(horizons)

        assert not result.is_valid
        assert any("non-numeric" in err.lower() for err in result.errors)

    def test_inverted_depths(self, invalid_horizons_inverted):
        """Test validation with inverted depths."""
        result = validate_horizon_sequence(invalid_horizons_inverted)

        assert not result.is_valid
        assert any("inverted" in err.lower() for err in result.errors)

    def test_depth_gap_warning(self, invalid_horizons_gap):
        """Test that depth gaps produce warnings."""
        result = validate_horizon_sequence(invalid_horizons_gap)

        assert result.is_valid  # Still valid, just warning
        assert any("gap" in w.lower() for w in result.warnings)

    def test_depth_overlap_warning(self, invalid_horizons_overlap):
        """Test that depth overlaps produce warnings."""
        result = validate_horizon_sequence(invalid_horizons_overlap)

        assert result.is_valid  # Still valid, just warning
        assert any("overlap" in w.lower() for w in result.warnings)

    def test_zero_thickness_horizon(self):
        """Test horizon with zero thickness."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20},
            {"hzname": "Bt", "upper": 20, "lower": 20},  # Zero thickness
        ]

        result = validate_horizon_sequence(horizons)

        assert not result.is_valid
        assert any(
            "zero thickness" in err.lower() or "equal" in err.lower() for err in result.errors
        )

    def test_very_thin_horizon_warning(self):
        """Test that very thin horizons produce warnings."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20},
            {"hzname": "Bt", "upper": 20, "lower": 20.2},  # 0.2 cm thick
        ]

        result = validate_horizon_sequence(horizons)

        assert any("thin" in w.lower() for w in result.warnings)

    def test_nan_values_warning(self):
        """Test that NaN values produce warnings."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20, "clay": np.nan},
            {"hzname": "Bt", "upper": 20, "lower": 50, "clay": 35.0},
        ]

        result = validate_horizon_sequence(horizons)

        assert any("nan" in w.lower() for w in result.warnings)

    def test_very_deep_horizon(self):
        """Test horizons exceeding typical depth."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20},
            {"hzname": "C", "upper": 20, "lower": 500},  # Very deep
        ]

        result = validate_horizon_sequence(horizons)

        # Non-strict mode should warn
        assert any("exceeds" in w.lower() for w in result.warnings)

        # Strict mode should error
        result_strict = validate_horizon_sequence(horizons, strict=True)
        assert any("exceeds" in e.lower() for e in result_strict.errors)


class TestMassPreservation:
    """Test validate_mass_preservation function."""

    def test_perfect_preservation(self):
        """Test with perfectly preserved mass."""
        assert validate_mass_preservation(100.0, 100.0)

    def test_within_tolerance(self):
        """Test mass within acceptable tolerance."""
        # 1% error (greater than default 0.0001% tolerance)
        original = 100.0
        splined = 100.0 * 1.0001  # Just barely outside tolerance

        # This should fail with default tolerance
        assert not validate_mass_preservation(original, splined, tolerance=1e-6)

        # But pass with relaxed tolerance
        assert validate_mass_preservation(original, splined, tolerance=1e-3)

    def test_zero_mass(self):
        """Test with zero mass."""
        assert validate_mass_preservation(0.0, 0.0)
        assert not validate_mass_preservation(0.0, 1.0)

    def test_large_mass_preservation(self):
        """Test with large mass values."""
        original = 1e6
        splined = original * (1 + 1e-7)  # 0.00001% error

        assert validate_mass_preservation(original, splined, tolerance=1e-6)

    def test_negative_mass(self):
        """Test with negative masses (edge case)."""
        assert validate_mass_preservation(-100.0, -100.0)
        assert not validate_mass_preservation(-100.0, -101.0)

    def test_different_tolerance_levels(self):
        """Test different tolerance specifications."""
        original = 100.0
        splined = 99.8  # 0.2% error = 2e-3

        # Should fail with strict tolerance
        assert not validate_mass_preservation(original, splined, tolerance=1e-3)

        # Should pass with relaxed tolerance
        assert validate_mass_preservation(original, splined, tolerance=1e-2)
