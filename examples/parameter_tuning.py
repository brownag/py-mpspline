"""
Parameter tuning example: Understand and adjust the smoothing parameter.

This example demonstrates how different parameter choices affect the
spline fitting and shows how to set value constraints.
"""

from mpspline import mpspline

# Define a soil profile with variable clay content
profile = {
    'cokey': 7001,
    'compname': 'Variable Soil',
    'horizons': [
        {'hzname': 'Ap', 'upper': 0, 'lower': 15, 'clay': 20.0},
        {'hzname': 'BA', 'upper': 15, 'lower': 25, 'clay': 28.0},
        {'hzname': 'Bt1', 'upper': 25, 'lower': 45, 'clay': 42.0},
        {'hzname': 'Bt2', 'upper': 45, 'lower': 65, 'clay': 40.0},
        {'hzname': 'BC', 'upper': 65, 'lower': 85, 'clay': 32.0},
    ]
}

target_depths = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 100)]

print("=" * 70)
print("Parameter Tuning Example")
print("=" * 70)

print("\nProfile horizons:")
print("-" * 70)
print(f"{'Horizon':<12} {'Depth (cm)':<15} {'Clay (%)':<12}")
print("-" * 70)
for hz in profile['horizons']:
    depth_range = f"{hz['upper']}-{hz['lower']}"
    print(f"{hz['hzname']:<12} {depth_range:<15} {hz['clay']:<12.1f}")

# Example 1: High smoothing (lam = 0.01)
print("\n" + "=" * 70)
print("1. HIGH SMOOTHING (lam = 0.01)")
print("-" * 70)
print("Use when: Data is noisy or you want conservative estimates")
print()

result_smooth = mpspline(
    profile,
    var_name=['clay'],
    target_depths=target_depths,
    lam=0.01
)

print(f"{'Depth Interval':<20} {'Clay (%)':<12}")
print("-" * 32)
for top, bottom in target_depths:
    key = f'clay_{top}_{bottom}'
    value = result_smooth[key]
    print(f"{top:>3}-{bottom:<3} cm {'':<7} {value:>6.2f}%")

# Example 2: Medium smoothing (lam = 0.1) [DEFAULT]
print("\n" + "=" * 70)
print("2. MEDIUM SMOOTHING (lam = 0.1) [DEFAULT]")
print("-" * 70)
print("Use when: Data quality is good, want balanced fit")
print()

result_medium = mpspline(
    profile,
    var_name=['clay'],
    target_depths=target_depths,
    lam=0.1
)

print(f"{'Depth Interval':<20} {'Clay (%)':<12}")
print("-" * 32)
for top, bottom in target_depths:
    key = f'clay_{top}_{bottom}'
    value = result_medium[key]
    print(f"{top:>3}-{bottom:<3} cm {'':<7} {value:>6.2f}%")

# Example 3: Low smoothing (lam = 1.0)
print("\n" + "=" * 70)
print("3. LOW SMOOTHING (lam = 1.0)")
print("-" * 70)
print("Use when: Data is accurate and you want close fit to observations")
print()

result_rough = mpspline(
    profile,
    var_name=['clay'],
    target_depths=target_depths,
    lam=1.0
)

print(f"{'Depth Interval':<20} {'Clay (%)':<12}")
print("-" * 32)
for top, bottom in target_depths:
    key = f'clay_{top}_{bottom}'
    value = result_rough[key]
    print(f"{top:>3}-{bottom:<3} cm {'':<7} {value:>6.2f}%")

# Example 4: Using constraints (clay % should be 0-100)
print("\n" + "=" * 70)
print("4. CONSTRAINED RESULTS (vlow=0, vhigh=100)")
print("-" * 70)
print("Use constraints to enforce realistic ranges for soil properties")
print()

result_constrained = mpspline(
    profile,
    var_name=['clay'],
    target_depths=target_depths,
    lam=0.1,
    vlow=0.0,      # Minimum: 0%
    vhigh=100.0    # Maximum: 100%
)

print(f"{'Depth Interval':<20} {'Clay (%)':<12}")
print("-" * 32)
for top, bottom in target_depths:
    key = f'clay_{top}_{bottom}'
    value = result_constrained[key]
    print(f"{top:>3}-{bottom:<3} cm {'':<7} {value:>6.2f}%")

# Comparison
print("\n" + "=" * 70)
print("5. COMPARISON TABLE")
print("=" * 70)
print(f"{'Depth':<12} {'Smooth(0.01)':<16} {'Medium(0.1)':<16} {'Rough(1.0)':<16}")
print("-" * 60)
for top, bottom in target_depths:
    key = f'clay_{top}_{bottom}'
    smooth_val = result_smooth[key]
    medium_val = result_medium[key]
    rough_val = result_rough[key]
    print(f"{top:>3}-{bottom:<3} cm  {smooth_val:>14.2f}%  {medium_val:>14.2f}%  {rough_val:>14.2f}%")

print("\n" + "=" * 70)
print("Key Takeaways:")
print("-" * 70)
print("• Lower lambda = more smoothing, less variance in predictions")
print("• Higher lambda = closer fit to original data")
print("• Use constraints (vlow/vhigh) to enforce realistic ranges")
print("• Default (lam=0.1) works well for most applications")
print("=" * 70)
