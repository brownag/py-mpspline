"""
Tests for parallel processing functionality.

Ensures that multiprocessing works correctly and handles pickling of
worker functions and arguments.
"""

import pandas as pd

from mpspline.spline import mpspline


class TestParallelHarmonization:
    """Test parallel processing in mpspline."""

    def test_parallel_processing_execution(self, multiple_components):
        """
        Test that parallel processing runs without error.

        This explicitly tests the fix for the pickling error.
        """
        df = mpspline(
            multiple_components,
            parallel=True,
            n_workers=2,  # Use 2 workers to ensure multiprocessing is used
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

        # Verify results match sequential execution (roughly)
        # Note: Floating point differences might exist, but structure should match

        # Check that splined columns are present and populated
        clay_cols = [c for c in df.columns if c.startswith("clay_")]
        assert len(clay_cols) > 0
        assert not df[clay_cols].isna().all().all()

    def test_parallel_vs_sequential_consistency(self, multiple_components):
        """Test that parallel and sequential results are identical."""
        # Run sequential
        df_seq = mpspline(multiple_components, parallel=False)

        # Run parallel
        df_par = mpspline(multiple_components, parallel=True, n_workers=2)

        # Sort by cokey to ensure alignment
        df_seq = df_seq.sort_values("cokey").reset_index(drop=True)
        df_par = df_par.sort_values("cokey").reset_index(drop=True)

        # Compare DataFrames
        pd.testing.assert_frame_equal(df_seq, df_par)

    def test_parallel_with_large_batch(self, miami_soil):
        """
        Test parallel processing with a generated larger dataset.

        This helps verify that passing data to workers works for more items.
        """
        # Create 20 duplicates of miami_soil with different cokeys
        components = []
        for i in range(20):
            comp = miami_soil.copy()
            comp["cokey"] = 1000 + i
            components.append(comp)

        df = mpspline(
            components,
            parallel=True,
            n_workers=4,
            batch_size=5,  # Small batch size to force multiple batches if implemented
        )

        assert len(df) == 20
        assert df["cokey"].nunique() == 20

    def test_parallel_error_handling(self, miami_soil):
        """Test that errors in parallel workers are handled correctly."""
        # Create a component that will fail (missing horizons)
        bad_comp = {"cokey": 99999}  # No horizons

        components = [miami_soil, bad_comp, miami_soil]

        # Should log warning but continue for valid components
        df = mpspline(components, parallel=True, strict=False)

        # Should have 2 successful results (the 2 copies of miami_soil)
        assert len(df) == 2
