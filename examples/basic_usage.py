"""
Basic usage example: Harmonize a single soil profile.

This example demonstrates how to use mpspline() to harmonize horizon data
from a single soil profile to standardized depth intervals.
"""

from mpspline import mpspline

# Define a single soil profile with horizons
profile = {
    'cokey': 12345,
    'compname': 'Miami',
    'taxorder': 'Alfisols',
    'horizons': [
        {
            'hzname': 'Ap',
            'upper': 0,
            'lower': 20,
            'clay': 24.5,
            'sand': 42.3,
            'silt': 33.2,
        },
        {
            'hzname': 'Bt',
            'upper': 20,
            'lower': 50,
            'clay': 35.2,
            'sand': 28.1,
            'silt': 36.7,
        },
        {
            'hzname': 'BC',
            'upper': 50,
            'lower': 80,
            'clay': 32.0,
            'sand': 35.0,
            'silt': 33.0,
        },
    ]
}

# Harmonize the profile to GlobalSoilMap standard depths
# (0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm)
result = mpspline(
    profile,
    var_name=['clay', 'sand', 'silt'],
    lam=0.1  # Use default smoothing parameter
)

print("=" * 60)
print("Basic mpspline Usage Example")
print("=" * 60)
print(f"\nProfile: {result['compname']} (cokey: {result['cokey']})")
print(f"Taxorder: {result['taxorder']}\n")

# Display harmonized clay percentages
print("Harmonized Clay Content (%):")
print("-" * 40)
for depth_name in ['0_5', '5_15', '15_30', '30_60', '60_100', '100_200']:
    key = f'clay_{depth_name}'
    if key in result:
        top, bottom = depth_name.split('_')
        value = result[key]
        print(f"  {top:>3}-{bottom:<3} cm: {value:>6.2f}%")

print("\nHarmonized Sand Content (%):")
print("-" * 40)
for depth_name in ['0_5', '5_15', '15_30', '30_60', '60_100', '100_200']:
    key = f'sand_{depth_name}'
    if key in result:
        top, bottom = depth_name.split('_')
        value = result[key]
        print(f"  {top:>3}-{bottom:<3} cm: {value:>6.2f}%")

print("\n" + "=" * 60)
print("✓ Harmonization complete!")
print("=" * 60)
