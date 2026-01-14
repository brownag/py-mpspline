"""Tests for parallel processing functionality."""

import pandas as pd

from mpspline.spline import mpspline


class TestParallelHarmonization:
    """Test parallel processing in mpspline."""

    def test_parallel_processing_execution(self, multiple_components):
        """Verify parallel processing runs without pickling errors."""
        df = mpspline(
            multiple_components,
            parallel=True,
            n_workers=2,
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) > len(multiple_components)
        assert df["cokey"].nunique() == len(multiple_components)
        assert "var_name" in df.columns
        assert not df["value"].isna().all()

    def test_parallel_vs_sequential_consistency(self, multiple_components):
        """Verify parallel and sequential results are identical."""
        df_seq = mpspline(multiple_components, parallel=False)
        df_par = mpspline(multiple_components, parallel=True, n_workers=2)

        # Sort to align records for long format comparison
        sort_cols = ["cokey", "var_name", "upper"]
        df_seq = df_seq.sort_values(sort_cols).reset_index(drop=True)
        df_par = df_par.sort_values(sort_cols).reset_index(drop=True)

        pd.testing.assert_frame_equal(df_seq, df_par)

    def test_parallel_with_large_batch(self, miami_soil):
        """Verify worker data passing with a larger dataset."""
        components = []
        for i in range(20):
            comp = miami_soil.copy()
            comp["cokey"] = 1000 + i
            components.append(comp)

        df = mpspline(
            components,
            parallel=True,
            n_workers=4,
            batch_size=5,
        )

        assert df["cokey"].nunique() == 20
        assert len(df) > 20

    def test_parallel_error_handling(self, miami_soil):
        """Verify non-strict mode skips problematic components in parallel."""
        bad_comp = {"cokey": 99999}  # Missing horizons
        components = [miami_soil, bad_comp, miami_soil]

        df = mpspline(components, parallel=True, strict=False)

        # Expected length is 2x single component output
        one_comp_len = len(mpspline([miami_soil]))
        assert len(df) == one_comp_len * 2
