"""
Custom depth intervals example: Harmonize to user-defined depths.

This example demonstrates how to specify custom depth intervals
instead of using the default GlobalSoilMap standard.
"""

from mpspline import mpspline

# Define a soil profile
profile = {
    'cokey': 5001,
    'compname': 'Well-Drained Soil',
    'horizons': [
        {'hzname': 'A', 'upper': 0, 'lower': 15, 'clay': 18.0, 'sand': 55.0},
        {'hzname': 'B', 'upper': 15, 'lower': 45, 'clay': 32.0, 'sand': 40.0},
        {'hzname': 'C', 'upper': 45, 'lower': 90, 'clay': 28.0, 'sand': 45.0},
    ]
}

print("=" * 70)
print("Custom Depth Intervals Example")
print("=" * 70)

# Example 1: GlobalSoilMap standard (default)
print("\n1. GlobalSoilMap Standard Depths (default):")
print("-" * 70)
default_depths = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200)]
print(f"Depths: {default_depths}")

result_default = mpspline(profile, var_name=['clay'])
print("\nHarmonized Clay (%):")
for depth in default_depths:
    top, bottom = depth
    key = f'clay_{top}_{bottom}'
    if key in result_default:
        print(f"  {top:>3}-{bottom:<3} cm: {result_default[key]:>6.2f}%")

# Example 2: Shallow sampling (< 1 meter)
print("\n" + "=" * 70)
print("2. Shallow Sampling Depths (< 1m):")
print("-" * 70)
shallow_depths = [(0, 5), (5, 10), (10, 20), (20, 40)]
print(f"Depths: {shallow_depths}")

result_shallow = mpspline(
    profile,
    var_name=['clay'],
    target_depths=shallow_depths
)
print("\nHarmonized Clay (%):")
for depth in shallow_depths:
    top, bottom = depth
    key = f'clay_{top}_{bottom}'
    if key in result_shallow:
        print(f"  {top:>3}-{bottom:<3} cm: {result_shallow[key]:>6.2f}%")

# Example 3: Deep profile (> 2 meters)
print("\n" + "=" * 70)
print("3. Deep Profile Depths (> 2m):")
print("-" * 70)
deep_depths = [(0, 10), (10, 30), (30, 60), (60, 100), (100, 150), (150, 200)]
print(f"Depths: {deep_depths}")

result_deep = mpspline(
    profile,
    var_name=['clay'],
    target_depths=deep_depths
)
print("\nHarmonized Clay (%):")
for depth in deep_depths:
    top, bottom = depth
    key = f'clay_{top}_{bottom}'
    if key in result_deep:
        print(f"  {top:>3}-{bottom:<3} cm: {result_deep[key]:>6.2f}%")

# Example 4: Custom scientific intervals
print("\n" + "=" * 70)
print("4. Custom Scientific Intervals (pedogenic depths):")
print("-" * 70)
pedogenic_depths = [(0, 5), (5, 25), (25, 50), (50, 100)]
print(f"Depths: {pedogenic_depths}")
print("(O/A interface, A-horizon, B-horizon, C-horizon)")

result_pedogenic = mpspline(
    profile,
    var_name=['clay'],
    target_depths=pedogenic_depths
)
print("\nHarmonized Clay (%):")
for depth, label in zip(pedogenic_depths,
                        ['O/A', 'A', 'B', 'C']):
    top, bottom = depth
    key = f'clay_{top}_{bottom}'
    if key in result_pedogenic:
        print(f"  {label}-horizon ({top:>3}-{bottom:<3} cm): {result_pedogenic[key]:>6.2f}%")

print("\n" + "=" * 70)
print("✓ Custom depth examples complete!")
print("=" * 70)
