"""
Mass-preserving spline algorithm implementation.

Implements the Bishop et al. (1999) equal-area quadratic smoothing spline method
for interpolating soil properties across depth intervals.

This is a pure Python implementation of the mpspline2 R package algorithm,
with direct translation of:
- mpspline_est1: Parameter estimation
- mpspline_fit1: Spline fitting and prediction
- mpspline_rmse1: Error calculation

Reference:
    Bishop, T.F.A., McBratney, A.B., Laslett, G.M. (1999)
    Modelling soil attribute depth functions with equal-area quadratic
    smoothing splines. Geoderma 89(3-4): 185-208.
    https://doi.org/10.1016/S0016-7061(99)00003-8
"""

import logging
from typing import Any, cast

import numpy as np
import pandas as pd
from scipy import linalg

logger = logging.getLogger(__name__)


def _format_depth_names(depths_top: np.ndarray, depths_bottom: np.ndarray) -> list[str]:
    """
    Format depth interval names as zero-padded strings.

    Args:
        depths_top: Array of upper depth boundaries (cm)
        depths_bottom: Array of lower depth boundaries (cm)

    Returns:
        List of formatted names like ['000_005_cm', '005_015_cm', ...]
    """
    return [f"{int(t):03d}_{int(b):03d}_cm" for t, b in zip(depths_top, depths_bottom)]


# Module-level cache for spline matrices
# Key: (tuple(depths_top), tuple(depths_bottom), lam)
# Value: (Z, R_inv, Q, th, gp)
_MATRIX_CACHE: dict[
    tuple[tuple[float, ...], tuple[float, ...], float],
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray],
] = {}
_MAX_CACHE_SIZE = 1000


def _get_spline_matrices(
    depths_top: tuple[float, ...],
    depths_bottom: tuple[float, ...],
    lam: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Get or compute spline matrices for a given depth pattern.

    Caches R, Q, Z matrices to avoid recomputation.
    """
    cache_key = (depths_top, depths_bottom, lam)

    if cache_key in _MATRIX_CACHE:
        cached = _MATRIX_CACHE[cache_key]
        return cached

    # If cache is full, clear it (simple strategy)
    if len(_MATRIX_CACHE) > _MAX_CACHE_SIZE:
        _MATRIX_CACHE.clear()

    # Convert tuples back to arrays for calculation
    dt = np.array(depths_top)
    db = np.array(depths_bottom)

    n = len(dt)
    nb = n - 1

    # Calculate thicknesses
    th = db - dt

    # Calculate gaps
    gp = np.zeros(nb)
    for i in range(nb):
        gp[i] = dt[i + 1] - db[i]

    # ========== Build Matrices ==========
    R = np.zeros((nb, nb))
    diag_values = 2 * (th[:-1] + th[1:]) + 6 * gp
    np.fill_diagonal(R, diag_values)

    # Off-diagonal: thickness[2:n-1]
    for i in range(nb - 1):
        R[i, i + 1] = R[i + 1, i] = th[i + 1]

    # Build Q matrix
    Q = np.zeros((nb, n))
    for i in range(nb):
        Q[i, i] = -1
        Q[i, i + 1] = 1

    # ========== Build and Solve Z Matrix ==========
    try:
        R_inv = linalg.inv(R)
    except np.linalg.LinAlgError:
        logger.warning("R matrix singular, using pseudo-inverse")
        R_inv = np.linalg.pinv(R)

    # Z = I + 6*n*lam * Q^T * R^-1 * Q
    identity = np.eye(n)
    QT_Rinv_Q = Q.T @ R_inv @ Q
    Z = identity + 6 * n * lam * QT_Rinv_Q

    # Store in cache
    result = (Z, R_inv, Q, th, gp)
    _MATRIX_CACHE[cache_key] = result

    return result


def _estimate_spline_parameters(
    depths_top: np.ndarray,
    depths_bottom: np.ndarray,
    values: np.ndarray,
    lam: float = 0.1,
) -> dict[str, np.ndarray | list[str]]:
    """
    Estimate spline parameters using Bishop et al. (1999) method.

    This implements mpspline_est1 from the R package. Solves the linear system
    to obtain smoothed values at knot points and spline coefficients.

    Args:
        depths_top: Array of upper boundaries for measured intervals (cm)
        depths_bottom: Array of lower boundaries for measured intervals (cm)
        values: Array of measured values for each interval
        lam: Smoothing parameter (default 0.1)

    Returns:
        Dictionary with keys:
        - 's_bar': Smoothed values at knot points
        - 'b': Spline curvature parameters
        - 'b0': Boundary coefficients (lower)
        - 'b1': Boundary coefficients (upper)
        - 'gamma': Linear coefficients for cubic polynomial
        - 'alfa': Constant coefficients for cubic polynomial
        - 'depth_names': Formatted depth interval names
    """
    dt_tuple = tuple(depths_top.astype(float))
    db_tuple = tuple(depths_bottom.astype(float))

    Z, R_inv, Q, th, gp = _get_spline_matrices(dt_tuple, db_tuple, lam)

    n = len(dt_tuple)

    # Solve Z * s_bar = values
    try:
        s_bar = linalg.solve(Z, values)
    except np.linalg.LinAlgError:
        logger.warning("Z matrix singular, using least squares")
        s_bar = np.linalg.lstsq(Z, values, rcond=None)[0]

    # ========== Calculate Spline Coefficients ==========
    b = 6 * R_inv @ Q @ s_bar
    b0 = np.concatenate([[0], b])  # coefficients at upper boundaries
    b1 = np.concatenate([b, [0]])  # coefficients at lower boundaries

    # gamma[i] = (b1[i] - b0[i]) / (2 * thickness[i])
    gamma = (b1 - b0) / (2 * th)

    # alfa[i] = s_bar[i] - b0[i] * thickness[i] / 2 - gamma[i] * thickness[i]^2 / 3
    alfa = s_bar - b0[:n] * th / 2 - gamma[:n] * (th**2) / 3

    # Format depth interval names
    depth_names = _format_depth_names(depths_top, depths_bottom)

    return {
        "s_bar": s_bar,
        "b": b,
        "b0": b0,
        "b1": b1,
        "gamma": gamma,
        "alfa": alfa,
        "depth_names": depth_names,
        "th": th,
        "gp": gp,
        "depths_top": depths_top,
        "depths_bottom": depths_bottom,
    }


def _fit_spline_predictions(
    params: dict,
    max_depth: int,
    target_depths: list[tuple[int, int]],
    vlow: float = 0.0,
    vhigh: float = 1000.0,
) -> dict[str, np.ndarray | float]:
    """
    Fit spline and generate predictions at target depth intervals.

    This implements mpspline_fit1 from the R package. Uses estimated parameters
    to generate 1cm predictions, then averages to target intervals.

    Args:
        params: Dictionary from _estimate_spline_parameters
        max_depth: Maximum depth to predict to (cm)
        target_depths: List of (top, bottom) tuples for output intervals
        vlow: Minimum constraint on predictions
        vhigh: Maximum constraint on predictions

    Returns:
        Dictionary with keys:
        - 'est_1cm': Predictions at every 1cm depth
        - 'est_dcm': Predictions averaged to target depth intervals
        - 'names_dcm': Names of output intervals
    """
    # Extract parameters
    depths_top = params["depths_top"]
    depths_bottom = params["depths_bottom"]
    alfa = params["alfa"]
    b0 = params["b0"]
    b1 = params["b1"]
    gamma = params["gamma"]

    # Initialize 1cm predictions array
    depths_arr = np.arange(max_depth, dtype=float)
    est_1cm = np.full(max_depth, np.nan)

    # Find interval indices for each depth
    # idx[i] is such that depths_top[idx[i]-1] <= depths_arr[i] < depths_top[idx[i]]
    # We want index h such that depths_top[h] <= depth < depths_bottom[h]

    # Use searchsorted to find potential interval starts
    # side='right' gives index i where a[i-1] <= v < a[i]
    # So idx - 1 is the index of the start depth <= current depth
    idx = np.searchsorted(depths_top, depths_arr, side="right") - 1

    # Valid indices are >= 0 and < n
    n = len(depths_top)
    valid_idx_mask = (idx >= 0) & (idx < n)

    # Check if depth is actually within the interval (depth < bottom)
    # Be careful with mask indexing
    in_interval_mask = np.zeros(max_depth, dtype=bool)
    in_interval_mask[valid_idx_mask] = (
        depths_arr[valid_idx_mask] < depths_bottom[idx[valid_idx_mask]]
    )

    # --- Calculate predictions within intervals ---
    if np.any(in_interval_mask):
        h_indices = idx[in_interval_mask]
        d_rel = depths_arr[in_interval_mask] - depths_top[h_indices]
        # prediction = alfa[h] + b0[h]*d_rel + gamma[h]*(d_rel^2)
        est_1cm[in_interval_mask] = (
            alfa[h_indices] + b0[h_indices] * d_rel + gamma[h_indices] * (d_rel**2)
        )

    # --- Calculate predictions in gaps ---
    gap_mask = ~in_interval_mask

    if np.any(gap_mask):
        gap_depths = depths_arr[gap_mask]

        # Find neighboring intervals
        prev_idx = np.searchsorted(depths_bottom, gap_depths, side="right") - 1
        next_idx = np.searchsorted(depths_top, gap_depths, side="left")
        valid_gap = (prev_idx >= 0) & (next_idx < n)

        if np.any(valid_gap):
            gap_indices = np.where(gap_mask)[0][valid_gap]
            p_h, n_h = prev_idx[valid_gap], next_idx[valid_gap]
            curr_depths = depths_arr[gap_indices]

            # Linear interpolation in gaps
            phi = alfa[n_h] - b1[p_h] * (depths_top[n_h] - depths_bottom[p_h])
            est_1cm[gap_indices] = phi + b1[p_h] * (curr_depths - depths_bottom[p_h])

    # ========== Apply Constraints and Average ==========
    np.clip(est_1cm, vlow, vhigh, out=est_1cm)

    est_dcm, names_dcm = [], []
    for depth_top, depth_bottom in target_depths:
        name = f"{depth_top:03d}_{depth_bottom:03d}_cm"
        names_dcm.append(name)

        if depth_top >= max_depth:
            est_dcm.append(np.nan)
            continue

        # Determine slice bounds
        start = depth_top
        end = min(depth_bottom, max_depth)

        if start < end:
            # Check for all-NaN slice to avoid RuntimeWarning
            slice_vals = est_1cm[start:end]
            if np.isnan(slice_vals).all():
                est_dcm.append(np.nan)
            else:
                est_dcm.append(np.nanmean(slice_vals))
        else:
            est_dcm.append(np.nan)

    est_dcm_array = np.array(est_dcm)

    return cast(
        dict[str, Any],
        {
            "est_1cm": est_1cm,
            "est_dcm": est_dcm_array,
            "names_dcm": names_dcm,
        },
    )


def _calculate_rmse(
    values: np.ndarray,
    fitted: np.ndarray,
) -> tuple[float, float]:
    """
    Calculate RMSE and RMSE scaled by IQR.

    This implements mpspline_rmse1 from the R package.

    Args:
        values: Original measured values
        fitted: Fitted/smoothed values

    Returns:
        Tuple of (RMSE, RMSE_IQR)
    """
    # Remove NaN values for comparison
    mask = ~(np.isnan(values) | np.isnan(fitted))
    if np.sum(mask) == 0:
        return np.nan, np.nan

    values_clean = values[mask]
    fitted_clean = fitted[mask]

    # RMSE
    rmse = np.sqrt(np.mean((values_clean - fitted_clean) ** 2))

    # RMSE scaled by IQR
    iqr = np.percentile(values_clean, 75) - np.percentile(values_clean, 25)
    if iqr > 0:
        rmse_iqr = rmse / iqr
    else:
        rmse_iqr = np.nan

    return float(rmse), float(rmse_iqr)


def _validate_and_prepare_data(
    df: pd.DataFrame,
    var_name: str,
    depth_col_top: str = "UD",
    depth_col_bottom: str = "LD",
) -> pd.DataFrame | None:
    """
    Validate and prepare horizon data for spline processing.

    This implements mpspline_datchk from the R package.

    Args:
        df: DataFrame with horizon data
        var_name: Column name of variable to process
        depth_col_top: Column name for upper depth
        depth_col_bottom: Column name for lower depth

    Returns:
        Cleaned DataFrame or None if validation fails
    """
    # Make a copy to avoid modifying original
    s = df.copy()

    # Drop rows with missing target variable
    if s[var_name].isna().all():
        logger.warning(f"All values missing for {var_name}")
        return None

    s = s[s[var_name].notna()].copy()

    if len(s) < 2:
        logger.warning(f"Less than 2 valid horizons for {var_name}")
        return None

    # Replace missing upper depth of first row with 0
    if s[depth_col_top].iloc[0] is None or pd.isna(s[depth_col_top].iloc[0]):
        s.loc[s.index[0], depth_col_top] = 0

    # Replace missing lower depth of last row with deepest UD + 10
    if s[depth_col_bottom].iloc[-1] is None or pd.isna(s[depth_col_bottom].iloc[-1]):
        deepest_ud = s[depth_col_top].max()
        s.loc[s.index[-1], depth_col_bottom] = deepest_ud + 10

    # Remove rows with negative depths (organic horizons)
    s = s[(s[depth_col_top] >= 0) & (s[depth_col_bottom] >= 0)]

    # Remove zero-thickness depth ranges
    s = s[s[depth_col_bottom] > s[depth_col_top]]

    # Remove inverted depths (UD > LD)
    s = s[s[depth_col_top] < s[depth_col_bottom]]

    # Sort by upper depth, then lower depth
    s = s.sort_values([depth_col_top, depth_col_bottom]).reset_index(drop=True)

    # Check for overlaps
    for i in range(len(s) - 1):
        if s[depth_col_bottom].iloc[i] > s[depth_col_top].iloc[i + 1]:
            logger.warning("Overlapping depth ranges detected")
            return None

    return s


def spline_one(
    df: pd.DataFrame,
    var_name: str,
    lam: float = 0.1,
    depth_col_top: str = "UD",
    depth_col_bottom: str = "LD",
    target_depths: list[tuple[int, int]] | None = None,
    vlow: float = 0.0,
    vhigh: float = 1000.0,
) -> dict[str, np.ndarray | list[str] | float]:
    """
    Fit mass-preserving spline for a single soil profile.

    Implements mpspline_one from the R package.

    Args:
        df: DataFrame with horizon data
        var_name: Column name of variable to spline
        lam: Smoothing parameter (default 0.1)
        depth_col_top: Column name for upper depth boundaries
        depth_col_bottom: Column name for lower depth boundaries
        target_depths: List of (top, bottom) tuples for output intervals
                      Default: GlobalSoilMap standard (0-5, 5-15, ..., 100-200)
        vlow: Minimum constraint on predictions (default 0)
        vhigh: Maximum constraint on predictions (default 1000)

    Returns:
        Dictionary with keys:
        - 'est_dcm': Array of predictions at target depth intervals
        - 'names_dcm': Names of output intervals
        - 'est_1cm': Array of predictions at every 1cm
        - 'rmse': Root mean squared error
        - 'rmse_iqr': RMSE scaled by interquartile range
    """
    from .constants import GLOBALSM_DEPTHS

    if target_depths is None:
        target_depths = GLOBALSM_DEPTHS

    # Validate and prepare data
    s = _validate_and_prepare_data(df, var_name, depth_col_top, depth_col_bottom)
    if s is None:
        return {
            "est_dcm": np.full(len(target_depths), np.nan),
            "names_dcm": [f"{t:03d}_{b:03d}_cm" for t, b in target_depths],
            "est_1cm": np.array([]),
            "rmse": np.nan,
            "rmse_iqr": np.nan,
        }

    # Extract and validate depths and values
    depths_top = s[depth_col_top].values.astype(float)
    depths_bottom = s[depth_col_bottom].values.astype(float)
    values = s[var_name].values.astype(float)

    # Handle single horizon case
    if len(depths_top) == 1:
        # No splining possible with single horizon
        logger.warning("Single horizon - no splining possible")
        return {
            "est_dcm": np.full(len(target_depths), values[0]),
            "names_dcm": [f"{t:03d}_{b:03d}_cm" for t, b in target_depths],
            "est_1cm": np.full(int(depths_bottom[0]), values[0]),
            "rmse": 0.0,
            "rmse_iqr": 0.0,
        }

    # Estimate spline parameters
    params = _estimate_spline_parameters(depths_top, depths_bottom, values, lam=lam)

    # Fit spline and generate predictions
    max_depth = int(max(depths_bottom, key=float)) + 1
    predictions = _fit_spline_predictions(params, max_depth, target_depths, vlow=vlow, vhigh=vhigh)

    # Calculate error metrics
    est_at_input: np.ndarray = params["s_bar"]  # type: ignore
    rmse, rmse_iqr = _calculate_rmse(values, est_at_input)

    return {
        "est_dcm": predictions["est_dcm"],
        "names_dcm": predictions["names_dcm"],
        "est_1cm": predictions["est_1cm"],
        "rmse": rmse,
        "rmse_iqr": rmse_iqr,
    }


def spline_multiple(
    df: pd.DataFrame,
    var_name: str | list[str],
    lam: float = 0.1,
    sid_col: str = "SID",
    depth_col_top: str = "UD",
    depth_col_bottom: str = "LD",
    target_depths: list[tuple[int, int]] | None = None,
    vlow: float = 0.0,
    vhigh: float = 1000.0,
) -> dict[str, dict]:
    """
    Fit mass-preserving splines for multiple soil profiles.

    Implements mpspline from the R package for multiple sites and/or variables.

    Args:
        df: DataFrame with horizon data for one or more sites
        var_name: Column name(s) of variable(s) to spline
        lam: Smoothing parameter (default 0.1)
        sid_col: Column name for site/profile identifier
        depth_col_top: Column name for upper depth boundaries
        depth_col_bottom: Column name for lower depth boundaries
        target_depths: List of (top, bottom) tuples for output intervals
        vlow: Minimum constraint on predictions
        vhigh: Maximum constraint on predictions

    Returns:
        Dictionary organized by variable name (if multiple) and site ID,
        with structure: result[var_name][site_id] = spline result dict
    """
    from .constants import GLOBALSM_DEPTHS

    if target_depths is None:
        target_depths = GLOBALSM_DEPTHS

    # Normalize var_name to list
    var_names = [var_name] if isinstance(var_name, str) else var_name

    # Group data by site ID
    sites = {site_id: group.reset_index(drop=True) for site_id, group in df.groupby(sid_col)}

    # Process each variable
    results = {}

    for v_name in var_names:
        if v_name not in df.columns:
            logger.warning(f"Column {v_name} not found in DataFrame")
            continue

        site_results = {}

        for site_id, site_df in sites.items():
            try:
                result = spline_one(
                    site_df,
                    var_name=v_name,
                    lam=lam,
                    depth_col_top=depth_col_top,
                    depth_col_bottom=depth_col_bottom,
                    target_depths=target_depths,
                    vlow=vlow,
                    vhigh=vhigh,
                )
                site_results[str(site_id)] = result

            except Exception as e:
                logger.error(f"Error processing site {site_id}, variable {v_name}: {e}")
                site_results[str(site_id)] = {
                    "est_dcm": np.full(len(target_depths), np.nan),
                    "names_dcm": [f"{t:03d}_{b:03d}_cm" for t, b in target_depths],
                    "est_1cm": np.array([]),
                    "rmse": np.nan,
                    "rmse_iqr": np.nan,
                }

        results[v_name] = site_results

    # If single variable, unwrap one level
    if len(var_names) == 1:
        return results[var_names[0]]

    return results
