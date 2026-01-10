"""
Batch processing example: Harmonize multiple soil profiles.

This example demonstrates how to use mpspline() to efficiently process
multiple soil profiles and return results as a pandas DataFrame.
"""

from mpspline import mpspline
import pandas as pd

# Define multiple soil profiles
profiles = [
    {
        'cokey': 1001,
        'compname': 'Miami',
        'taxorder': 'Alfisols',
        'horizons': [
            {'hzname': 'Ap', 'upper': 0, 'lower': 20, 'clay': 24.5, 'silt': 33.2},
            {'hzname': 'Bt', 'upper': 20, 'lower': 50, 'clay': 35.2, 'silt': 36.7},
            {'hzname': 'BC', 'upper': 50, 'lower': 80, 'clay': 32.0, 'silt': 33.0},
        ]
    },
    {
        'cokey': 1002,
        'compname': 'Crosby',
        'taxorder': 'Mollisols',
        'horizons': [
            {'hzname': 'Ap', 'upper': 0, 'lower': 25, 'clay': 28.0, 'silt': 45.0},
            {'hzname': 'Bt', 'upper': 25, 'lower': 60, 'clay': 38.5, 'silt': 42.0},
        ]
    },
    {
        'cokey': 1003,
        'compname': 'Drummer',
        'taxorder': 'Mollisols',
        'horizons': [
            {'hzname': 'Ap', 'upper': 0, 'lower': 22, 'clay': 26.0, 'silt': 50.0},
            {'hzname': 'A', 'upper': 22, 'lower': 38, 'clay': 27.0, 'silt': 51.0},
            {'hzname': 'Bg', 'upper': 38, 'lower': 70, 'clay': 32.0, 'silt': 48.0},
        ]
    },
]

print("=" * 70)
print("Batch Processing Example")
print("=" * 70)
print(f"\nProcessing {len(profiles)} soil profiles...")
print("Using: mpspline(profiles, var_name=['clay', 'silt'], parallel=False)\n")

# Process all profiles at once (returns pandas DataFrame)
df = mpspline(
    profiles,
    var_name=['clay', 'silt'],
    parallel=False,  # Set to True for parallel processing with multiple CPU cores
    batch_size=10,
)

print("Results DataFrame (first 8 columns):")
print("-" * 70)
print(df.iloc[:, :8].to_string())

print("\n" + "-" * 70)
print(f"\nDataFrame shape: {df.shape}")
print(f"Columns ({len(df.columns)}): {', '.join(df.columns[:10])}...")

print("\n" + "=" * 70)
print("Summary Statistics - Clay Content (%)")
print("=" * 70)
clay_cols = [col for col in df.columns if col.startswith('clay_')]
print(df[clay_cols].describe().round(2))

print("\n" + "=" * 70)
print("✓ Batch processing complete!")
print("=" * 70)

# Optional: Try parallel processing (uncomment to enable)
# print("\n\nTesting parallel processing...")
# df_parallel = mpspline(
#     profiles,
#     var_name=['clay', 'silt'],
#     parallel=True,      # Use multiprocessing
#     n_workers=2,        # Use 2 CPU cores
#     batch_size=10,
# )
# print("✓ Parallel processing works! Same results as sequential.")
