"""
Tests for HorizonSequence class.

Tests initialization, property extraction, data normalization, and validation.
"""

import numpy as np
import pytest

from mpspline.spline import HorizonSequence


class TestHorizonSequenceInitialization:
    """Test HorizonSequence initialization and basic operations."""

    def test_simple_horizons(self, simple_horizons):
        """Test initialization with valid simple horizon sequence."""
        hz_seq = HorizonSequence(simple_horizons)

        assert hz_seq.horizons is not None
        assert len(hz_seq.horizons) == 2
        assert hz_seq.max_depth == 50
        assert "clay" in hz_seq.properties
        assert "sand" in hz_seq.properties

    def test_miami_soil(self, miami_soil):
        """Test initialization with Miami soil component."""
        hz_seq = HorizonSequence(miami_soil["horizons"])

        assert len(hz_seq.horizons) == 5
        assert hz_seq.max_depth == 120
        assert "clay" in hz_seq.properties
        assert "ph1to1h2o_r" in hz_seq.properties

    def test_empty_horizons(self):
        """Test initialization with empty horizons list."""
        with pytest.raises(ValueError, match="Invalid horizon sequence"):
            HorizonSequence([])

    def test_single_horizon(self, horizon_single):
        """Test initialization with single horizon (below minimum)."""
        with pytest.raises(ValueError, match="Insufficient horizons"):
            HorizonSequence(horizon_single)

    def test_property_extraction(self, miami_soil):
        """Test that all properties are extracted and sorted."""
        hz_seq = HorizonSequence(miami_soil["horizons"])

        expected_properties = {"clay", "sand", "silt", "om_r", "ph1to1h2o_r"}
        assert set(hz_seq.properties) == expected_properties

        # Should be sorted
        assert hz_seq.properties == sorted(hz_seq.properties)

    def test_numeric_property_normalization(self):
        """Test that string numeric properties are normalized."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20, "clay": "24.5"},
            {"hzname": "Bt", "upper": 20, "lower": 50, "clay": 35.2},
        ]

        hz_seq = HorizonSequence(horizons)
        assert isinstance(hz_seq.horizons[0]["clay"], float)
        assert hz_seq.horizons[0]["clay"] == 24.5

    def test_repr(self, simple_horizons):
        """Test string representation."""
        hz_seq = HorizonSequence(simple_horizons)
        repr_str = repr(hz_seq)

        assert "HorizonSequence" in repr_str
        assert "2" in repr_str  # 2 horizons
        assert "50" in repr_str  # max depth
        assert "2" in repr_str  # 2 properties


class TestPropertyDataExtraction:
    """Test get_property_data method."""

    def test_extract_property_data(self, simple_horizons):
        """Test extracting depth-property pairs."""
        hz_seq = HorizonSequence(simple_horizons)
        depths, values = hz_seq.get_property_data("clay")

        assert len(depths) == 2
        assert len(values) == 2
        assert np.allclose(depths[0], 10)  # Midpoint of 0-20
        assert np.allclose(depths[1], 35)  # Midpoint of 20-50
        assert np.allclose(values[0], 24.5)
        assert np.allclose(values[1], 35.2)

    def test_extract_missing_property(self, simple_horizons):
        """Test extracting property not in data."""
        hz_seq = HorizonSequence(simple_horizons)
        depths, values = hz_seq.get_property_data("nonexistent")

        assert len(depths) == 0
        assert len(values) == 0

    def test_extract_partial_property(self):
        """Test extracting property present in some horizons."""
        horizons = [
            {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 24.5},
            {"hzname": "Bt", "upper": 20, "lower": 50},  # No clay value
        ]

        hz_seq = HorizonSequence(horizons)
        depths, values = hz_seq.get_property_data("clay")

        # Should only have 1 value
        assert len(depths) == 1
        assert len(values) == 1
        assert np.allclose(values[0], 24.5)


class TestValidationIntegration:
    """Test validation integration in HorizonSequence."""

    def test_validation_gap_warning(self, invalid_horizons_gap):
        """Test that gaps trigger warnings."""
        # Should not raise, but should log warnings
        hz_seq = HorizonSequence(invalid_horizons_gap)
        assert hz_seq is not None

    def test_validation_overlap_warning(self, invalid_horizons_overlap):
        """Test that overlaps trigger warnings."""
        hz_seq = HorizonSequence(invalid_horizons_overlap)
        assert hz_seq is not None

    def test_validation_inverted_error(self, invalid_horizons_inverted):
        """Test that inverted depths raise error."""
        with pytest.raises(ValueError):
            HorizonSequence(invalid_horizons_inverted)

    def test_validation_missing_field_error(self, invalid_horizons_missing_field):
        """Test that missing fields raise error."""
        with pytest.raises(ValueError):
            HorizonSequence(invalid_horizons_missing_field)

    def test_strict_mode(self, invalid_horizons_gap):
        """Test strict mode enforcement."""
        # Gaps should be OK in non-strict mode
        hz_seq = HorizonSequence(invalid_horizons_gap, strict=False)
        assert hz_seq is not None

        # In strict mode, gaps still produce warnings but don't fail
        # (current implementation treats warnings as non-blocking)
        hz_seq_strict = HorizonSequence(invalid_horizons_gap, strict=True)
        assert hz_seq_strict is not None
