"""
Tests for component harmonization functions.

Tests mpspline_one() and mpspline() with various
input data and validation scenarios.
"""

import numpy as np
import pandas as pd
import pytest

from mpspline.spline import mpspline, mpspline_one


class TestHarmonizeComponent:
    """Test mpspline_one function with default (Long) output."""

    def test_simple_component_harmonization(self, simple_horizons):
        """Test basic harmonization with simple horizons."""
        component = {
            "cokey": 1234,
            "compname": "Test",
            "horizons": simple_horizons,
        }

        # Default is long format (list of dicts)
        result = mpspline_one(component)

        assert isinstance(result, list)
        assert len(result) > 0

        # Check metadata preserved in records
        assert result[0]["cokey"] == 1234
        assert result[0]["compname"] == "Test"

        # Check properties exist
        clay_records = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_records) > 0

        # Verify structure
        first = clay_records[0]
        assert "upper" in first
        assert "lower" in first
        assert "value" in first

    def test_miami_soil_harmonization(self, miami_soil):
        """Test harmonization of Miami soil component."""
        result = mpspline_one(miami_soil)

        # Check metadata
        assert result[0]["cokey"] == miami_soil["cokey"]

        # Check all properties are processed
        found_vars = {r["var_name"] for r in result}
        expected_vars = {"clay", "sand", "silt", "om_r", "ph1to1h2o_r"}
        assert expected_vars.issubset(found_vars)

    def test_custom_target_depths(self, simple_horizons):
        """Test harmonization with custom depth intervals."""
        component = {"cokey": 123, "horizons": simple_horizons}
        custom_depths = [(0, 10), (10, 30), (30, 50)]

        result = mpspline_one(component, target_depths=custom_depths)

        # Check clay records match depth count
        clay_records = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_records) == 3

        # Verify specific depths
        assert clay_records[0]["upper"] == 0
        assert clay_records[0]["lower"] == 10

    def test_specific_properties(self, simple_horizons):
        """Test harmonization with specific properties."""
        component = {"cokey": 123, "horizons": simple_horizons}

        result = mpspline_one(component, var_name=["clay", "sand"])

        found_vars = {r["var_name"] for r in result}
        assert "clay" in found_vars
        assert "sand" in found_vars
        assert "silt" not in found_vars

    def test_invalid_horizons_handling(self):
        """Test handling of invalid horizon sequences."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "Ap", "upper": 50, "lower": 20},  # Inverted
            ],
        }

        # Should raise in strict mode
        with pytest.raises(ValueError):
            mpspline_one(component, strict=True)

        # Should return empty list in non-strict mode (default for long format error)
        result = mpspline_one(component, strict=False)
        assert result == []

    def test_missing_property_handling(self):
        """Test handling when requested property doesn't exist."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
                {"hzname": "Bt", "upper": 20, "lower": 50, "clay": 35.0},
            ],
        }

        # Request properties that don't exist
        result = mpspline_one(component, var_name=["nonexistent", "clay"])

        found_vars = {r["var_name"] for r in result}
        assert "clay" in found_vars
        assert "nonexistent" not in found_vars

    def test_partial_property_data(self):
        """Test handling when property is missing from some horizons."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
                {"hzname": "Bt", "upper": 20, "lower": 50},  # No clay
                {"hzname": "BC", "upper": 50, "lower": 80, "clay": 28.0},
            ],
        }

        result = mpspline_one(component, strict=False)

        # Should contain some clay records (interpolated)
        clay_records = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_records) > 0


class TestWideFormat:
    """Test optional wide format output."""

    def test_wide_output_format(self, simple_horizons):
        """Test output format and column naming for wide format."""
        component = {"cokey": 123, "compname": "Test", "horizons": simple_horizons}
        result = mpspline_one(component, output_type="wide")

        assert isinstance(result, dict)
        assert result["cokey"] == 123

        # Check column keys
        clay_keys = [k for k in result.keys() if k.startswith("clay_")]
        assert len(clay_keys) > 0
        assert "clay_0_5" in result

    def test_mass_preservation_conceptual_wide(self, miami_soil):
        """Test wide format specific keys."""
        result = mpspline_one(miami_soil, output_type="wide")

        for prop in ["clay", "sand", "silt"]:
            prop_cols = [k for k in result.keys() if k.startswith(f"{prop}_")]
            assert len(prop_cols) > 0


class TestHarmonizeComponentsBulk:
    """Test mpspline function (returns DataFrame)."""

    def test_bulk_multiple_components(self, multiple_components):
        """Test bulk processing (default long format)."""
        df = mpspline(multiple_components)

        assert isinstance(df, pd.DataFrame)
        # Should be much longer than input list
        assert len(df) > len(multiple_components)

        expected_cols = ["cokey", "compname", "var_name", "upper", "lower", "value"]
        for col in expected_cols:
            assert col in df.columns

    def test_bulk_empty_list(self):
        """Test bulk processing with empty component list."""
        df = mpspline([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_bulk_single_component(self, miami_soil):
        """Test bulk processing with single component."""
        df = mpspline([miami_soil])
        assert len(df) > 0
        assert df.iloc[0]["cokey"] == miami_soil["cokey"]

    def test_bulk_batch_processing(self, multiple_components):
        """Test bulk processing with batching."""
        df = mpspline(multiple_components, batch_size=1)
        # Check basic count (3 profiles * ~5 vars * 6 depths ~= 90 rows)
        assert len(df) > 50

    def test_bulk_with_custom_depths(self, multiple_components):
        """Test bulk processing with custom depths."""
        custom_depths = [(0, 20), (20, 50)]
        df = mpspline(multiple_components, target_depths=custom_depths)

        # Verify depths in output
        assert set(df["upper"].unique()) == {0, 20}
        assert set(df["lower"].unique()) == {20, 50}

    def test_bulk_wide_format(self, multiple_components):
        """Test bulk processing requesting wide format."""
        df = mpspline(multiple_components, output_type="wide")

        assert len(df) == 3
        assert "clay_0_5" in df.columns


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_single_horizon_component(self):
        """Test component with single horizon (below minimum)."""
        component = {
            "cokey": 123,
            "horizons": [{"hzname": "A", "upper": 0, "lower": 20, "clay": 25.0}],
        }

        with pytest.raises(ValueError):
            mpspline_one(component, strict=True)

        # Default long format returns empty list for failed components
        result = mpspline_one(component, strict=False)
        assert result == []

    def test_all_nan_property(self):
        """Test handling of property with all NaN values."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "A", "upper": 0, "lower": 20, "clay": np.nan},
                {"hzname": "B", "upper": 20, "lower": 50, "clay": np.nan},
            ],
        }

        result = mpspline_one(component, strict=False)

        # Should return records with NaN values
        clay_records = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_records) > 0
        for r in clay_records:
            assert np.isnan(r["value"])

    def test_unicode_in_horizon_names(self):
        """Test handling of unicode characters in horizon names."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
                {"hzname": "Bt (oxidized)", "upper": 20, "lower": 50, "clay": 35.0},
            ],
        }

        result = mpspline_one(component, strict=False)
        assert len(result) > 0
        assert result[0]["cokey"] == 123


class TestModes:
    """Test different output modes (dcm, 1cm, icm)."""

    def test_1cm_mode(self, simple_horizons):
        """Test 1cm resolution mode."""
        component = {"cokey": 1234, "horizons": simple_horizons}
        df = mpspline([component], mode="1cm")

        assert "depth" in df.columns
        assert "value" in df.columns

        # Count numeric properties (clay, sand, silt, om_r = 4)
        prop_count = 4

        # algorithm.py fits up to max(depths_bottom) + 1
        # max depth is 50cm -> 0-50 inclusive indices = 51 points?
        # Actually 0-1, ..., 49-50.
        # Check actual logic: np.arange(max_depth) where max_depth = int(max_bottom) + 1
        # So for 50.0, max_depth is 51. range is 0..50.
        max_depth = int(max(h["lower"] for h in simple_horizons))
        assert len(df) == (max_depth + 1) * prop_count

    def test_icm_mode(self, simple_horizons):
        """Test input interval mode."""
        component = {"cokey": 1234, "horizons": simple_horizons}
        df = mpspline([component], mode="icm")

        assert "upper" in df.columns
        assert "lower" in df.columns

        # Should have 1 record per original horizon per property
        # 2 horizons * 4 properties = 8 records
        assert len(df) == 8
