Algorithm Overview
===================

This page explains the algorithm behind mpspline.

Background
----------

mpspline implements the mass-preserving equal-area quadratic smoothing spline algorithm described in:

Bishop, T.F.A., McBratney, A.B., & Laslett, G.M. (1999). *Modelling soil attribute depth functions with equal-area quadratic smoothing splines.* Geoderma, 89(3-4), 185-208.

What It Does
~~~~~~~~~~~~

Given soil horizon data at varying depths, the algorithm:

1. Fits a smooth function through the data
2. Generates 1cm predictions across the profile depth
3. Averages predictions to standardized depth intervals
4. **Preserves mass**: Average values at standard depths equal the original data

Why It Matters
~~~~~~~~~~~~~~

Soil data is usually collected at irregular depths (horizons):

.. code-block:: text

    Depth (cm)    Clay (%)
    0-20          24.5      ← Ap horizon
    20-50         35.2      ← Bt horizon
    50-80         32.0      ← BC horizon

But analysis often requires standardized depths:

.. code-block:: text

    Depth (cm)    Clay (%)
    0-5           21.4      ← Interpolated
    5-15          24.1      ← Interpolated
    15-30         29.8      ← Interpolated
    30-60         34.9      ← Interpolated
    60-100        31.2      ← Interpolated

The spline algorithm ensures these new estimates have the same **average** value as the original horizons.

How It Works
~~~~~~~~~~~~

The algorithm has three main steps:

**Step 1: Estimate Spline Parameters**

- Fit a continuous function using quadratic spline pieces
- Each piece defined by parameters at control points
- Smoothing parameter (lambda) controls how tightly the spline fits

**Step 2: Generate Predictions**

- Use the fitted spline to predict values at 1cm intervals
- Creates a continuous depth function from discrete horizons
- Ensures mass is preserved across depth intervals

**Step 3: Aggregate to Standard Depths**

- Average predictions within each target depth interval
- Output harmonized values at standardized depths
- Result: Values that represent the horizon averages

Implementation Details
----------------------

This implementation strictly adheres to the mathematical derivation presented in **Appendix A** of Malone et al. (2009), ensuring accurate reproduction of the roughness penalty matrix :math:`\mathbf{R}`.

Specifically, the diagonal elements of the :math:`\mathbf{R}` matrix are constructed as:

.. math::

    R_{ii} = 2(h_i + h_{i+1}) + 6g_i

Where :math:`h_i` is the thickness of layer :math:`i` and :math:`g_i` is the gap between layers. This formulation is numerically consistent with the reference `mpspline2` R package.

Key Properties
--------------

**Mass Preservation**

The algorithm ensures:

.. math::

    \frac{\sum_{d_{top}}^{d_{bottom}} f(d)}{d_{bottom} - d_{top}} = \text{original average}

In plain English: The average of the spline function across the original horizon depth equals the original value.

**Smoothing Parameter (Lambda)**

Controls the trade-off between smoothness and fit:

- **Small lambda** (0.001-0.01): Very smooth predictions
- **Default lambda** (0.1): Balanced smoothness and fit
- **Large lambda** (1.0-10.0): Closer fit to original data

**Continuity**

The function is:
- Continuous: No jumps
- Smooth: No sharp angles
- Differentiable: Can compute slopes

Parameters That Matter
---------------------

**lambda (lam)**

Smoothing parameter (default: 0.1)

Controls the trade-off between:
- **Smoothness**: Smaller lambda = smoother curve
- **Fidelity**: Larger lambda = follows data more closely

Example:

.. code-block:: python

    # Smooth curve for noisy data
    result = mpspline(profile, lam=0.01)

    # Balanced (default)
    result = mpspline(profile, lam=0.1)

    # Follows data closely
    result = mpspline(profile, lam=1.0)

**vlow and vhigh**

Value constraints (default: 0.0 and 1000.0)

Ensures predictions stay within realistic ranges:

.. code-block:: python

    # Clay: 0-100%
    result = mpspline(profile, var_name=['clay'], vlow=0, vhigh=100)

    # Bulk density: 1-2 g/cm³
    result = mpspline(
        profile,
        var_name=['bdensity'],
        vlow=1.0,
        vhigh=2.0
    )

Strengths
---------

1. **Mass preservation**: Maintains original horizon averages
2. **Smooth predictions**: No artificial discontinuities
3. **Flexibility**: Works with any horizon configuration
4. **Robustness**: Handles variable number of horizons
5. **Speed**: Efficient computation

Limitations
-----------

1. **Extrapolation**: Cannot extend beyond profile depth
2. **Few horizons**: Requires minimum 2 horizons per profile
3. **Assumption**: Assumes smooth depth function (not appropriate for all properties)
4. **Parameter selection**: Choice of lambda affects results

When to Use Different Lambda Values
------------------------------------

**Use lambda = 0.01 (smooth):**
- Noisy field measurements
- Estimate is uncertain
- Want conservative, smooth predictions
- Variability between horizons seems excessive

**Use lambda = 0.1 (default):**
- Normal soil profile data
- Good data quality
- Want balanced fit
- When in doubt, use this

**Use lambda = 1.0 (fit close to data):**
- Very accurate laboratory measurements
- High precision data
- Want predictions close to observed values
- Large number of horizons with clear trends

Algorithm Diagram
-----------------

Simplified flow:

.. code-block:: text

    Input Horizons
         ↓
    Estimate Spline Parameters (using lambda)
         ↓
    Generate Predictions at 1cm intervals
         ↓
    Apply Constraints (vlow, vhigh)
         ↓
    Aggregate to Standard Depths
         ↓
    Output Harmonized Values

Example Walkthrough
-------------------

Given this profile:

.. code-block:: text

    Horizon  | Depth    | Clay
    ---------|----------|------
    Ap       | 0-20cm   | 24.5%
    Bt       | 20-50cm  | 35.2%

**Step 1**: Fit spline function

The algorithm finds parameters that:
- Pass through (0, 24.5) and (20, 24.5) boundary
- Pass through (20, 35.2) and (50, 35.2) boundary
- Smooth transition between horizons
- Controlled by lambda parameter

**Step 2**: Generate 1cm predictions

Spline function evaluated at every 1cm:

.. code-block:: text

    Depth  | Prediction
    -------|----------
    0-1cm  | 24.1%
    1-2cm  | 24.2%
    ...
    20-21cm| 28.5%
    ...
    50cm   | 35.2%

**Step 3**: Aggregate to standard depths

Average predictions within intervals:

.. code-block:: text

    Interval    | Average of Predictions
    ------------|---------------------
    0-5cm       | (24.1+24.2+...)/5 = 24.3%
    5-15cm      | (average of 5-15)  = 24.5%
    15-30cm     | (average of 15-30) = 28.9%
    30-60cm     | (average of 30-60) = 35.0%

Result: Harmonized values that preserve original horizon averages!

Further Reading
---------------

- Bishop et al. (1999): Original algorithm paper https://doi.org/10.1016/S0016-7061(99)00003-8
- Malone et al. (2009): Application to soil carbon mapping https://doi.org/10.1016/j.geoderma.2009.10.007
- mpspline2 R package: Reference implementation https://github.com/obrl-soil/mpspline2
