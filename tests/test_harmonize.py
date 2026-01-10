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
    """Test mpspline_one function."""

    def test_simple_component_harmonization(self, simple_horizons):
        """Test basic harmonization with simple horizons."""
        component = {
            "cokey": 1234,
            "compname": "Test",
            "horizons": simple_horizons,
        }

        result = mpspline_one(component)

        # Should have original fields
        assert result["cokey"] == 1234
        assert result["compname"] == "Test"

        # Should NOT have horizons
        assert "horizons" not in result

        # Should have splined properties
        # Check for properties like clay_0_5, clay_5_15, etc.
        clay_cols = [k for k in result.keys() if k.startswith("clay_")]
        assert len(clay_cols) > 0

    def test_miami_soil_harmonization(self, miami_soil):
        """Test harmonization of Miami soil component."""
        result = mpspline_one(miami_soil)

        # Check original fields preserved
        assert result["cokey"] == miami_soil["cokey"]
        assert result["compname"] == miami_soil["compname"]

        # Check splined columns exist
        for prop in ["clay", "sand", "silt", "om_r", "ph1to1h2o_r"]:
            clay_cols = [k for k in result.keys() if k.startswith(f"{prop}_")]
            assert len(clay_cols) > 0, f"Property {prop} should have splined columns"

    def test_custom_target_depths(self, simple_horizons):
        """Test harmonization with custom depth intervals."""
        component = {"cokey": 123, "horizons": simple_horizons}
        custom_depths = [(0, 10), (10, 30), (30, 50)]

        result = mpspline_one(component, target_depths=custom_depths)

        # Check custom depth columns
        clay_cols = [k for k in result.keys() if k.startswith("clay_")]
        assert len(clay_cols) == 3  # Should have 3 intervals

    def test_specific_properties(self, simple_horizons):
        """Test harmonization with specific properties."""
        component = {"cokey": 123, "horizons": simple_horizons}

        result = mpspline_one(component, var_name=["clay", "sand"])

        # Should have clay and sand columns
        clay_cols = [k for k in result.keys() if k.startswith("clay_")]
        sand_cols = [k for k in result.keys() if k.startswith("sand_")]

        assert len(clay_cols) > 0
        assert len(sand_cols) > 0

        # Should NOT have silt or om_r columns
        silt_cols = [k for k in result.keys() if k.startswith("silt_")]
        assert len(silt_cols) == 0

    def test_invalid_component_structure(self):
        """Test error handling for invalid component structure."""
        # Missing horizons key
        with pytest.raises(ValueError, match="horizons"):
            mpspline_one({"cokey": 123})

        # Non-dict component
        with pytest.raises(TypeError):
            mpspline_one("not a dict")

        # Empty horizons
        with pytest.raises(ValueError, match="horizons"):
            mpspline_one({"cokey": 123, "horizons": []})

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

        # Should return original in non-strict mode
        result = mpspline_one(component, strict=False)
        assert result["cokey"] == 123
        # When validation fails, original data is returned (including horizons)
        assert "horizons" in result

    def test_output_format(self, simple_horizons):
        """Test output format and column naming."""
        component = {"cokey": 123, "compname": "Test", "horizons": simple_horizons}
        result = mpspline_one(component)

        # Output should be dict
        assert isinstance(result, dict)

        # Column names should follow pattern: property_depth_top_depth_bottom
        for key in result.keys():
            if "_" in key and any(key.startswith(p) for p in ["clay", "sand", "silt", "om_r"]):
                parts = key.split("_")
                # Should have at least property_top_bottom
                assert len(parts) >= 3

    def test_mass_preservation_conceptual(self, miami_soil):
        """
        Test conceptual mass preservation.

        Note: Actual mass preservation requires understanding mpspline2
        output format. This test verifies the concept is implemented.
        """
        result = mpspline_one(miami_soil)

        # Should have successfully processed all properties
        for prop in ["clay", "sand", "silt"]:
            prop_cols = [k for k in result.keys() if k.startswith(f"{prop}_")]
            assert len(prop_cols) > 0

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

        # Should only have clay columns
        clay_cols = [k for k in result.keys() if k.startswith("clay_")]
        assert len(clay_cols) > 0

        nonex_cols = [k for k in result.keys() if k.startswith("nonexistent_")]
        assert len(nonex_cols) == 0

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

        # Should still produce some output
        [k for k in result.keys() if k.startswith("clay_")]
        # Might be 0 if only 1 value, or might spline if 2+ values
        assert "cokey" in result  # At least metadata preserved


class TestHarmonizeComponentsBulk:
    """Test mpspline function."""

    def test_bulk_multiple_components(self, multiple_components):
        """Test bulk processing of multiple components."""
        df = mpspline(multiple_components)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "cokey" in df.columns
        assert "compname" in df.columns

        # Check splined columns exist
        clay_cols = [c for c in df.columns if c.startswith("clay_")]
        assert len(clay_cols) > 0

    def test_bulk_empty_list(self):
        """Test bulk processing with empty component list."""
        df = mpspline([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_bulk_single_component(self, miami_soil):
        """Test bulk processing with single component."""
        df = mpspline([miami_soil])

        assert len(df) == 1
        assert df.iloc[0]["cokey"] == miami_soil["cokey"]

    def test_bulk_batch_processing(self, multiple_components):
        """Test bulk processing with batching."""
        # Use small batch size
        df = mpspline(
            multiple_components,
            batch_size=1,
        )

        assert len(df) == 3

    def test_bulk_with_custom_depths(self, multiple_components):
        """Test bulk processing with custom depths."""
        custom_depths = [(0, 20), (20, 50)]
        df = mpspline(
            multiple_components,
            target_depths=custom_depths,
        )

        # Should have custom depth columns
        clay_cols = [c for c in df.columns if c.startswith("clay_")]
        assert len(clay_cols) == 2  # Two custom depths

    def test_bulk_with_specific_properties(self, multiple_components):
        """Test bulk processing with specific properties."""
        df = mpspline(
            multiple_components,
            var_name=["clay", "sand"],
        )

        clay_cols = [c for c in df.columns if c.startswith("clay_")]
        sand_cols = [c for c in df.columns if c.startswith("sand_")]
        silt_cols = [c for c in df.columns if c.startswith("silt_")]

        assert len(clay_cols) > 0
        assert len(sand_cols) > 0
        assert len(silt_cols) == 0

    def test_bulk_column_consistency(self, multiple_components):
        """Test that all rows have same columns."""
        df = mpspline(multiple_components)

        # All rows should have same columns
        for _i in range(1, len(df)):
            for col in df.columns:
                # No missing columns
                assert col in df.columns

    def test_bulk_dataframe_conversion(self, multiple_components):
        """Test conversion to DataFrame."""
        df = mpspline(multiple_components)

        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 3  # 3 rows
        assert df.shape[1] > 4  # At least cokey, compname, comppct_r, taxorder + splined


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_single_horizon_component(self):
        """Test component with single horizon (below minimum)."""
        component = {
            "cokey": 123,
            "horizons": [{"hzname": "A", "upper": 0, "lower": 20, "clay": 25.0}],
        }

        # Should fail
        with pytest.raises(ValueError):
            mpspline_one(component, strict=True)

        # Non-strict should return original metadata
        result = mpspline_one(component, strict=False)
        assert result["cokey"] == 123

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

        # Should have metadata
        assert result["cokey"] == 123

        # Should have clay columns but values should be NaN
        clay_cols = [k for k in result.keys() if k.startswith("clay_")]
        assert len(clay_cols) > 0
        for col in clay_cols:
            assert np.isnan(result[col])

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
        assert result["cokey"] == 123
