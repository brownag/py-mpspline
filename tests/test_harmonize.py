"""Tests for component harmonization functions."""

import numpy as np
import pandas as pd
import pytest

from mpspline.spline import mpspline, mpspline_one


class TestHarmonizeComponent:
    """Test mpspline_one function with default (Long) output."""

    def test_simple_component_harmonization(self, simple_horizons):
        """Verify basic harmonization logic and metadata preservation."""
        component = {
            "cokey": 1234,
            "compname": "Test",
            "horizons": simple_horizons,
        }

        result = mpspline_one(component)

        assert isinstance(result, list)
        assert result[0]["cokey"] == 1234
        assert result[0]["compname"] == "Test"

        clay_records = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_records) > 0
        assert all(k in clay_records[0] for k in ["upper", "lower", "value"])

    def test_miami_soil_harmonization(self, miami_soil):
        """Verify all standard properties are processed for Miami soil."""
        result = mpspline_one(miami_soil)
        found_vars = {r["var_name"] for r in result}
        expected_vars = {"clay", "sand", "silt", "om_r", "ph1to1h2o_r"}
        assert expected_vars.issubset(found_vars)

    def test_custom_target_depths(self, simple_horizons):
        """Verify harmonization to user-specified depth intervals."""
        component = {"cokey": 123, "horizons": simple_horizons}
        custom_depths = [(0, 10), (10, 30), (30, 50)]

        result = mpspline_one(component, target_depths=custom_depths)

        clay_records = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_records) == 3
        assert clay_records[0]["upper"] == 0
        assert clay_records[0]["lower"] == 10

    def test_specific_properties(self, simple_horizons):
        """Verify filtering of properties to process."""
        component = {"cokey": 123, "horizons": simple_horizons}
        result = mpspline_one(component, var_name=["clay", "sand"])

        found_vars = {r["var_name"] for r in result}
        assert "clay" in found_vars
        assert "sand" in found_vars
        assert "silt" not in found_vars

    def test_invalid_horizons_handling(self):
        """Verify error handling for invalid horizon sequences."""
        component = {
            "cokey": 123,
            "horizons": [{"hzname": "Ap", "upper": 50, "lower": 20}],
        }

        with pytest.raises(ValueError):
            mpspline_one(component, strict=True)

        # Long format returns empty list on failure in non-strict mode
        assert mpspline_one(component, strict=False) == []

    def test_missing_property_handling(self):
        """Verify skipping of non-existent properties."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "A", "upper": 0, "lower": 20, "clay": 25.0},
                {"hzname": "B", "upper": 20, "lower": 50, "clay": 35.0},
            ],
        }
        result = mpspline_one(component, var_name=["nonexistent", "clay"])
        found_vars = {r["var_name"] for r in result}
        assert "clay" in found_vars
        assert "nonexistent" not in found_vars

    def test_partial_property_data(self):
        """Verify interpolation when property is missing from some horizons."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "A", "upper": 0, "lower": 20, "clay": 25.0},
                {"hzname": "B", "upper": 20, "lower": 50},
                {"hzname": "C", "upper": 50, "lower": 80, "clay": 28.0},
            ],
        }
        result = mpspline_one(component, strict=False)
        assert any(r["var_name"] == "clay" for r in result)


class TestWideFormat:
    """Test optional wide format output for backward compatibility."""

    def test_wide_output_format(self, simple_horizons):
        """Verify flat dictionary structure when requesting wide format."""
        component = {"cokey": 123, "horizons": simple_horizons}
        result = mpspline_one(component, output_type="wide")

        assert isinstance(result, dict)
        assert "clay_0_5" in result

    def test_mass_preservation_conceptual_wide(self, miami_soil):
        """Verify expected keys exist in wide output for multiple properties."""
        result = mpspline_one(miami_soil, output_type="wide")
        for prop in ["clay", "sand", "silt"]:
            assert any(k.startswith(f"{prop}_") for k in result.keys())


class TestHarmonizeComponentsBulk:
    """Test mpspline function for multiple profiles."""

    def test_bulk_multiple_components(self, multiple_components):
        """Verify long format DataFrame output for multiple profiles."""
        df = mpspline(multiple_components)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > len(multiple_components)
        assert all(c in df.columns for c in ["var_name", "upper", "lower", "value"])

    def test_bulk_empty_list(self):
        """Verify empty list input returns empty DataFrame."""
        assert len(mpspline([])) == 0

    def test_bulk_single_component(self, miami_soil):
        """Verify list with single component returns populated DataFrame."""
        df = mpspline([miami_soil])
        assert len(df) > 0
        assert df.iloc[0]["cokey"] == miami_soil["cokey"]

    def test_bulk_batch_processing(self, multiple_components):
        """Verify batching logic in bulk processing."""
        df = mpspline(multiple_components, batch_size=1)
        # 3 components * 5 vars * 6 depths = 90 rows
        assert len(df) == 90

    def test_bulk_wide_format(self, multiple_components):
        """Verify wide format DataFrame output."""
        df = mpspline(multiple_components, output_type="wide")
        assert len(df) == len(multiple_components)
        assert "clay_0_5" in df.columns


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_single_horizon_component(self):
        """Verify failure for components with fewer than 2 horizons."""
        component = {
            "cokey": 123,
            "horizons": [{"hzname": "A", "upper": 0, "lower": 20, "clay": 25.0}],
        }
        with pytest.raises(ValueError):
            mpspline_one(component, strict=True)
        assert mpspline_one(component, strict=False) == []

    def test_all_nan_property(self):
        """Verify handling of properties with entirely NaN values."""
        component = {
            "cokey": 123,
            "horizons": [
                {"hzname": "A", "upper": 0, "lower": 20, "clay": np.nan},
                {"hzname": "B", "upper": 20, "lower": 50, "clay": np.nan},
            ],
        }
        result = mpspline_one(component, strict=False)
        clay_recs = [r for r in result if r["var_name"] == "clay"]
        assert len(clay_recs) > 0
        assert all(np.isnan(r["value"]) for r in clay_recs)


class TestModes:
    """Test different output modes (dcm, 1cm, icm)."""

    def test_1cm_mode(self, simple_horizons):
        """Verify high-resolution 1cm output mode."""
        df = mpspline([{"cokey": 1, "horizons": simple_horizons}], mode="1cm")
        assert "depth" in df.columns

        # Count numeric properties dynamically
        numeric_props = [
            k for k, v in simple_horizons[0].items() 
            if k not in ["hzname", "upper", "lower"] and isinstance(v, (int, float))
        ]
        prop_count = len(numeric_props)
        max_depth = int(max(h["lower"] for h in simple_horizons))
        assert len(df) == (max_depth + 1) * prop_count

    def test_icm_mode(self, simple_horizons):
        """Verify smoothed input interval output mode."""
        df = mpspline([{"cokey": 1, "horizons": simple_horizons}], mode="icm")
        # 2 horizons * 4 properties = 8 records
        assert len(df) == 8
