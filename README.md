# mpspline

Python implementation of mass-preserving equal-area quadratic splines for harmonizing soil profiles to standard depth intervals.

Port of the [mpspline2](https://github.com/obrl-soil/mpspline2) R package by Lauren O'Brien, based on the method of [Bishop et al. (1999)](https://doi.org/10.1016/S0016-7061(99)00003-8), as generalized in [Malone et al. (2009)](https://doi.org/10.1016/j.geoderma.2009.10.007).

## Installation

```bash
pip install mpspline
```

## Quick Start

```python
from mpspline import mpspline

# Single profile
result = mpspline({
    'horizons': [
        {'hzname': 'A', 'upper': 0, 'lower': 20, 'clay': 24.5},
        {'hzname': 'B', 'upper': 20, 'lower': 50, 'clay': 35.2},
    ]
})
print(result)  # {'clay_0_5': 21.4, 'clay_5_15': 27.8, ...}

# Multiple profiles
profiles = [...]
df = mpspline(profiles)  # Returns DataFrame
```

## Usage

Pass a dict for a single profile or a list for multiple profiles:

```python
from mpspline import mpspline

# Single profile (returns dict)
result = mpspline({
    'cokey': 12345,
    'horizons': [
        {'hzname': 'Ap', 'upper': 0, 'lower': 20, 'clay': 24.5},
        {'hzname': 'Bt', 'upper': 20, 'lower': 50, 'clay': 35.2},
    ]
})
print(result['clay_0_5'])  # 21.4

# Multiple profiles (returns DataFrame)
profiles = [
    {
        'cokey': 1001,
        'horizons': [
            {'hzname': 'A', 'upper': 0, 'lower': 15, 'clay': 18.5},
            {'hzname': 'Bt1', 'upper': 15, 'lower': 45, 'clay': 35.0},
            {'hzname': 'Bt2', 'upper': 45, 'lower': 80, 'clay': 32.5},
        ]
    },
    {
        'cokey': 1002,
        'horizons': [
            {'hzname': 'Ap', 'upper': 0, 'lower': 20, 'clay': 15.2},
            {'hzname': 'Bw', 'upper': 20, 'lower': 50, 'clay': 28.4},
            {'hzname': 'C', 'upper': 50, 'lower': 100, 'clay': 25.0},
        ]
    },
]
df = mpspline(profiles, var_name=['clay'], parallel=True)
print(df[['cokey', 'clay_0_5', 'clay_5_15', 'clay_15_30', 'clay_30_60']])
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `obj` | dict or list | Required | Profile(s) with a `'horizons'` key |
| `var_name` | str or list | None | Properties to harmonize (all numeric if None) |
| `target_depths` | list | GlobalSoilMap | Depth intervals as `(top, bottom)`. Default: `[(0,5), (5,15), (15,30), (30,60), (60,100), (100,200)]` |
| `lam` | float | 0.1 | Smoothing parameter (0.01=smooth, 1.0=fit data closely) |
| `vlow` | float | 0.0 | Minimum constraint for values |
| `vhigh` | float | 1000.0 | Maximum constraint for values |
| `parallel` | bool | False | Use multiprocessing for multiple profiles |
| `batch_size` | int | 100 | Profiles per batch |
| `strict` | bool | False | Raise exceptions on validation errors (False = skip) |

### Horizon Input Format

Required fields:
- Depth: `upper` and `lower` (or `top` and `bottom`) in cm
- Properties: numeric fields to harmonize

Optional:
- `hzname`: horizon name

Example:
```python
{
    'hzname': 'Ap',
    'upper': 0,
    'lower': 20,
    'clay': 24.5,
    'sand': 42.3,
}
```

## Examples

```python
# Custom depth intervals
result = mpspline(profile, target_depths=[(0, 10), (10, 30), (30, 60)])

# Adjust smoothing (0.01=smooth, 1.0=closer to data)
result = mpspline(profile, lam=0.01)

# Constrain values to realistic ranges
result = mpspline(profile, var_name=['clay'], vlow=0, vhigh=100)

# Parallel processing for many profiles
df = mpspline(profiles, parallel=True, batch_size=500)

# Only process specific properties
df = mpspline(profiles, var_name=['clay', 'sand'])

# Error handling: skip bad profiles or raise errors
df = mpspline(profiles, strict=False)  # Skip problematic profiles
try:
    df = mpspline(profiles, strict=True)  # Raise on errors
except ValueError as e:
    print(f"Validation error: {e}")
```

## Troubleshooting

**Horizons not ordered by depth**: Horizons must be sequential with no gaps or overlaps.
```python
# Wrong
{'upper': 0, 'lower': 30}, {'upper': 20, 'lower': 50}

# Right
{'upper': 0, 'lower': 20}, {'upper': 20, 'lower': 50}
```

**Values outside expected ranges**: Use `vlow` and `vhigh` to constrain predictions:
```python
result = mpspline(profile, vlow=0, vhigh=100)
```

**Processing is slow**: Enable parallel processing:
```python
df = mpspline(profiles, parallel=True, batch_size=500)
```

## How it works

The algorithm fits a mass-preserving equal-area quadratic spline to horizon data. This converts discrete observations at varying depths to standard depth intervals while preserving the average value across each depth range.

See the [algorithm documentation](https://py-mpspline.readthedocs.io/algorithm.html) for details.

## References

*   **O'Brien, L.** (2025). [mpspline2: Mass-Preserving Spline Functions for Soil Data](https://github.com/obrl-soil/mpspline2). R package version 0.1.9. https://doi.org/10.32614/CRAN.package.mpspline2
*   **Bishop, T.F.A., McBratney, A.B., & Laslett, G.M. (1999).** Modelling soil attribute depth functions with equal-area quadratic smoothing splines. *Geoderma*, 89(3-4), 185-208. https://doi.org/10.1016/S0016-7061(99)00003-8
*   **Malone, B.P., McBratney, A.B., & Minasny, B. (2009).** Mapping continuous depth functions of soil carbon storage and available water capacity. *Geoderma*, 154(3-4), 138-152. https://doi.org/10.1016/j.geoderma.2009.10.007

## License

GPL 3.0