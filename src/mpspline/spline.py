"""
Core spline harmonization module.

Implements mass-preserving equal-area quadratic spline interpolation for
depth harmonization of soil component profiles based on mpspline2 R package.

This module provides high-level APIs for harmonizing soil profiles:
- HorizonSequence: Class for managing and validating horizon data
- mpspline_one(): Single component harmonization (internal/low-level)
- mpspline(): Main entry point for single or bulk harmonization
- to_soilprofilecollection(): Convert results to SoilProfileCollection (optional)

Reference:
    Malone, B. P., McBratney, A. B., & Minasny, B. (2009). Mapping continuous
    depth functions of soil carbon storage and available water capacity.
    Geoderma, 154(3-4), 138-152.
"""

import logging
from copy import deepcopy
from multiprocessing import Pool
from typing import Any

import numpy as np
import pandas as pd

from .algorithm import spline_one
from .constants import GLOBALSM_DEPTHS
from .validation import validate_horizon_sequence

logger = logging.getLogger(__name__)

# Try to import soilprofilecollection
try:
    from soilprofilecollection import SoilProfileCollection

    HAS_SPC = True
except ImportError:
    HAS_SPC = False
    SoilProfileCollection = None


class HorizonSequence:
    """
    Represents a sequence of soil horizons for a component.

    Handles extraction and validation of horizon data, property identification,
    and preparation for spline interpolation.

    Attributes:
        horizons: List of horizon dictionaries
        max_depth: Maximum depth of any horizon (cm)
        properties: Sorted list of numeric properties across all horizons
    """

    def __init__(self, horizons: list[dict], strict: bool = False):
        """
        Initialize from horizon list.

        Args:
            horizons: List of horizon dicts with keys:
                - hzname: Horizon name (str)
                - upper: Depth to top (cm, int/float)
                - lower: Depth to bottom (cm, int/float)
                - [property names]: Property values (float)
            strict: If True, raise on validation errors instead of warnings
        """
        self.strict = strict

        # Standardize horizon keys (map common aliases to standard names)
        std_horizons = self._standardize_horizons(horizons)
        self.raw_horizons = std_horizons

        # Validate horizon sequence
        validation = validate_horizon_sequence(std_horizons, strict=strict)
        if not validation.is_valid:
            raise ValueError(f"Invalid horizon sequence: {', '.join(validation.errors)}")

        # Store validation warnings
        if validation.warnings:
            for warning in validation.warnings:
                logger.warning(f"Horizon sequence: {warning}")

        # Normalize horizon data (ensure numeric types)
        self.horizons = self._normalize_horizons(std_horizons)
        self.max_depth = max(h["lower"] for h in self.horizons)
        self.properties = self._extract_property_names()

    def _standardize_horizons(self, horizons: list[dict]) -> list[dict]:
        """Map common depth column names (top, upper, bottom, lower) to standardized fields."""
        standardized = []
        depth_top_aliases = {"top", "upper"}
        depth_bottom_aliases = {"bottom", "lower"}

        for i, hz in enumerate(horizons):
            new_hz = dict(hz)
            if "upper" not in new_hz:
                for alias in depth_top_aliases:
                    if alias in new_hz:
                        new_hz["upper"] = new_hz.pop(alias)
                        break

            if "lower" not in new_hz:
                for alias in depth_bottom_aliases:
                    if alias in new_hz:
                        new_hz["lower"] = new_hz.pop(alias)
                        break

            if "hzname" not in new_hz:
                if "name" in new_hz and isinstance(new_hz["name"], str):
                    new_hz["hzname"] = new_hz.pop("name")
                elif "label" in new_hz and isinstance(new_hz["label"], str):
                    new_hz["hzname"] = new_hz.pop("label")
                else:
                    new_hz["hzname"] = f"H{i + 1}"
            standardized.append(new_hz)
        return standardized

    def _normalize_horizons(self, horizons: list[dict]) -> list[dict]:
        """Normalize depths and numeric properties to float."""
        normalized = []
        for hz in horizons:
            norm_hz = dict(hz)
            norm_hz["upper"] = float(hz["upper"])
            norm_hz["lower"] = float(hz["lower"])

            for key, value in norm_hz.items():
                if key not in {"hzname", "upper", "lower"} and isinstance(value, str):
                    try:
                        norm_hz[key] = float(value)
                    except (ValueError, TypeError):
                        pass
            normalized.append(norm_hz)
        return normalized

    def _extract_property_names(self) -> list[str]:
        """
        Find all numeric properties across all horizons.

        Returns:
            Sorted list of property names (excludes depth fields)
        """
        standard_keys = {"hzname", "upper", "lower"}
        properties = set()

        for h in self.horizons:
            for k, v in h.items():
                if k not in standard_keys and isinstance(v, (int, float)):
                    properties.add(k)

        return sorted(properties)

    def get_property_data(self, property_name: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract depth-property pairs for a specific property.

        Returns:
            Tuple of (depths_array, values_array) where depths are midpoints
            of each horizon.
        """
        depths = []
        values = []

        for h in self.horizons:
            if property_name in h:
                value = h[property_name]
                if isinstance(value, (int, float)) and not (
                    isinstance(value, float) and np.isnan(value)
                ):
                    # Use midpoint depth
                    depth_mid = (h["upper"] + h["lower"]) / 2
                    depths.append(depth_mid)
                    values.append(value)

        if not depths:
            return np.array([]), np.array([])

        return np.array(depths), np.array(values)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert to DataFrame format suitable for spline processing.

        Returns:
            DataFrame with columns: 'UD' (upper depth), 'LD' (lower depth),
            and property columns
        """
        data = []
        for hz in self.horizons:
            row = {
                "UD": hz["upper"],
                "LD": hz["lower"],
            }
            # Add all numeric properties
            for prop in self.properties:
                if prop in hz:
                    row[prop] = hz[prop]
            data.append(row)

        return pd.DataFrame(data)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"HorizonSequence(n_horizons={len(self.horizons)}, "
            f"max_depth={self.max_depth} cm, "
            f"n_properties={len(self.properties)})"
        )


def mpspline_one(
    component_data: dict,
    var_name: str | list[str] | None = None,
    target_depths: list[tuple[int, int]] | None = None,
    lam: float = 0.1,
    vlow: float = 0.0,
    vhigh: float = 1000.0,
    strict: bool = False,
    output_type: str = "long",
    mode: str = "dcm",
) -> dict | list[dict]:
    """
    Harmonize a single component's horizons to standard depths.

    Applies mass-preserving quadratic spline interpolation to convert variable-depth
    horizon data into fixed-depth intervals.

    Args:
        component_data: Component dict with 'horizons' list.
        var_name: Property name(s) to spline. Default: all numeric properties.
        target_depths: (top, bottom) tuples in cm. Default: GlobalSoilMap.
        lam: Smoothing parameter (0.1 default).
        vlow, vhigh: Min/max prediction constraints.
        strict: Raise on validation errors (vs skip with warning).
        output_type: 'long' (list of dicts) or 'wide' (dict with columns).
        mode: 'dcm' (standard), '1cm' (every 1cm), 'icm' (input intervals).

    Returns:
        List[dict] if output_type='long', else dict.
    """
    if target_depths is None:
        target_depths = GLOBALSM_DEPTHS

    # Validate input
    if not isinstance(component_data, dict):
        raise TypeError("component_data must be a dict")

    if "horizons" not in component_data:
        raise ValueError("component_data must contain 'horizons' key")

    horizons = component_data["horizons"]
    if not horizons:
        raise ValueError("horizons list is empty")

    # Create HorizonSequence (validates horizons)
    try:
        hz_seq = HorizonSequence(horizons, strict=strict)
    except ValueError as e:
        if strict:
            raise
        logger.warning(f"Horizon sequence error: {e}")
        if output_type == "long":
            return []
        return deepcopy(component_data)

    # Determine which properties to spline
    if var_name is None:
        properties_to_process = hz_seq.properties
    elif isinstance(var_name, str):
        properties_to_process = [var_name] if var_name in hz_seq.properties else []
    else:
        properties_to_process = [p for p in var_name if p in hz_seq.properties]

    # Convert horizons to DataFrame for spline processing
    try:
        hz_df = hz_seq.to_dataframe()
    except Exception as e:
        if strict:
            raise
        logger.warning(f"Failed to convert horizons to DataFrame: {e}")
        if output_type == "long":
            return []
        return deepcopy(component_data)

    # Extract metadata (everything except horizons)
    metadata = {k: v for k, v in component_data.items() if k != "horizons"}

    # Container for long format results
    long_results = []

    # Container for wide format results (start with metadata)
    wide_result = deepcopy(metadata)

    # Process each property
    for property_name in properties_to_process:
        try:
            spline_result = spline_one(
                hz_df,
                var_name=property_name,
                lam=lam,
                target_depths=target_depths,
                vlow=vlow,
                vhigh=vhigh,
            )

            if output_type == "wide":
                # Wide format: flatten to column names with depth intervals
                if mode == "dcm":
                    names_dcm_wide: list[str] = spline_result["names_dcm"]  # type: ignore
                    est_dcm_wide: np.ndarray = spline_result["est_dcm"]  # type: ignore
                    for depth_name, value in zip(names_dcm_wide, est_dcm_wide):
                        parts = depth_name.rstrip("_cm").split("_")
                        depth_top = int(parts[0].lstrip("0") or "0")
                        depth_bottom = int(parts[1].lstrip("0") or "0")
                        key = f"{property_name}_{depth_top}_{depth_bottom}"
                        wide_result[key] = float(value) if not np.isnan(value) else np.nan

                elif mode == "1cm":
                    # 1cm mode: one column per cm depth (e.g., clay_0cm, clay_1cm, ...)
                    est_1cm: np.ndarray = spline_result["est_1cm"]  # type: ignore
                    for depth, value in enumerate(est_1cm):
                        key = f"{property_name}_{depth}cm"
                        wide_result[key] = float(value) if not np.isnan(value) else np.nan

                elif mode == "icm":
                    # ICM with wide format: create columns per input interval depth
                    est_icm: np.ndarray = spline_result["est_icm"]  # type: ignore
                    depths_top: np.ndarray = spline_result["depths_top"]  # type: ignore
                    depths_bottom: np.ndarray = spline_result["depths_bottom"]  # type: ignore

                    for i, value in enumerate(est_icm):
                        depth_top = int(depths_top[i])
                        depth_bottom = int(depths_bottom[i])
                        key = f"{property_name}_{depth_top}_{depth_bottom}"
                        wide_result[key] = float(value) if not np.isnan(value) else np.nan

            else:  # output_type == "long"
                if mode == "dcm":
                    names_dcm_long: list[str] = spline_result["names_dcm"]  # type: ignore
                    est_dcm_long: np.ndarray = spline_result["est_dcm"]  # type: ignore
                    for depth_name, value in zip(names_dcm_long, est_dcm_long):
                        parts = depth_name.rstrip("_cm").split("_")
                        record = deepcopy(metadata)
                        record["var_name"] = property_name
                        record["upper"] = int(parts[0].lstrip("0") or "0")
                        record["lower"] = int(parts[1].lstrip("0") or "0")
                        record["value"] = float(value) if not np.isnan(value) else np.nan
                        long_results.append(record)

                elif mode == "1cm":
                    est_1cm: np.ndarray = spline_result["est_1cm"]  # type: ignore
                    for depth, value in enumerate(est_1cm):
                        record = deepcopy(metadata)
                        record["var_name"] = property_name
                        record["depth"] = depth
                        record["value"] = float(value) if not np.isnan(value) else np.nan
                        long_results.append(record)

                elif mode == "icm":
                    est_icm: np.ndarray = spline_result["est_icm"]  # type: ignore
                    depths_top: np.ndarray = spline_result["depths_top"]  # type: ignore
                    depths_bottom: np.ndarray = spline_result["depths_bottom"]  # type: ignore

                    for i, value in enumerate(est_icm):
                        record = deepcopy(metadata)
                        record["var_name"] = property_name
                        record["upper"] = float(depths_top[i])
                        record["lower"] = float(depths_bottom[i])
                        record["value"] = float(value) if not np.isnan(value) else np.nan
                        long_results.append(record)

        except Exception as e:
            if strict:
                raise
            logger.warning(
                f"Spline error for property '{property_name}' "
                f"in component {component_data.get('cokey', 'unknown')}: {e}"
            )

    if output_type == "long":
        return long_results
    return wide_result


def mpspline(
    obj: dict | list[dict],
    var_name: str | list[str] | None = None,
    target_depths: list[tuple[int, int]] | None = None,
    lam: float = 0.1,
    vlow: float = 0.0,
    vhigh: float = 1000.0,
    batch_size: int = 100,
    parallel: bool = False,
    n_workers: int | None = None,
    strict: bool = False,
    output_type: str = "long",
    mode: str = "dcm",
) -> dict | pd.DataFrame:
    """
    Harmonize one or more soil components to standard depths.

    Args:
        obj: Single component dict or list of component dicts.
        var_name: Property name(s) to spline. Default: all numeric properties.
        target_depths: (top, bottom) tuples. Default: GlobalSoilMap.
        lam: Smoothing parameter (default 0.1).
        vlow, vhigh: Prediction constraints.
        batch_size: Process in batches (memory optimization).
        parallel: Use multiprocessing for bulk processing.
        n_workers: Number of worker processes. Default: CPU count.
        strict: If True, raise on errors; else skip problematic components.
        output_type: 'long' (default) or 'wide'.
            - 'long': DataFrame rows (one per depth interval per property)
            - 'wide': DataFrame columns (flattened, all modes supported)
        mode: Output depth intervals
            - 'dcm' (default): Standard GlobalSoilMap depths
            - '1cm': Every 1cm (note: wide format creates many columns)
            - 'icm': Input component horizons (original depth intervals)

    Returns:
        Dict or DataFrame of harmonized data.
    """
    if target_depths is None:
        target_depths = GLOBALSM_DEPTHS

    # Handle single dictionary input
    if isinstance(obj, dict):
        return mpspline_one(
            obj,
            var_name=var_name,
            target_depths=target_depths,
            lam=lam,
            vlow=vlow,
            vhigh=vhigh,
            strict=strict,
            output_type=output_type,
            mode=mode,
        )

    # Assume list of dicts for bulk processing
    components = obj

    if not isinstance(components, list):
        raise TypeError("obj must be a dict or a list of dicts")

    logger.info(
        f"Starting harmonization of {len(components)} components "
        f"(batch_size={batch_size}, parallel={parallel})"
    )

    # Process components
    if parallel:
        harmonized_batches = _process_parallel(
            components=components,
            var_name=var_name,
            target_depths=target_depths,
            lam=lam,
            vlow=vlow,
            vhigh=vhigh,
            n_workers=n_workers,
            strict=strict,
            output_type=output_type,
            mode=mode,
        )
    else:
        harmonized_batches = _process_sequential(
            components=components,
            var_name=var_name,
            target_depths=target_depths,
            lam=lam,
            vlow=vlow,
            vhigh=vhigh,
            strict=strict,
            output_type=output_type,
            mode=mode,
        )

    # Convert to DataFrame
    if not harmonized_batches:
        logger.warning("No components were successfully harmonized")
        return pd.DataFrame()

    # Aggregate results
    if output_type == "long":
        # Flatten list of lists
        flat_results = [item for sublist in harmonized_batches for item in sublist]
        df = pd.DataFrame(flat_results)
    else:
        # Wide format: list of dicts
        df = pd.DataFrame(harmonized_batches)

    logger.info(f"Successfully harmonized {len(df)} records")

    return df


def _process_sequential(
    components: list[dict],
    var_name: str | list[str] | None,
    target_depths: list[tuple[int, int]],
    lam: float,
    vlow: float,
    vhigh: float,
    strict: bool,
    output_type: str,
    mode: str,
) -> list:
    """Process components sequentially."""
    harmonized = []

    for i, component in enumerate(components):
        try:
            result = mpspline_one(
                component,
                var_name=var_name,
                target_depths=target_depths,
                lam=lam,
                vlow=vlow,
                vhigh=vhigh,
                strict=strict,
                output_type=output_type,
                mode=mode,
            )
            harmonized.append(result)

            if (i + 1) % 100 == 0:
                logger.debug(f"Processed {i + 1} components")

        except Exception as e:
            if strict:
                raise
            logger.warning(
                f"Failed to harmonize component {i} ({component.get('cokey', 'unknown')}): {e}"
            )

    return harmonized


def _harmonize_worker(
    component: dict,
    var_name: str | list[str] | None,
    target_depths: list[tuple[int, int]],
    lam: float,
    vlow: float,
    vhigh: float,
    strict: bool,
    output_type: str,
    mode: str,
) -> dict | list | None:
    """
    Worker function for multiprocessing.

    Must be at module level to be picklable.
    """
    try:
        return mpspline_one(
            component,
            var_name=var_name,
            target_depths=target_depths,
            lam=lam,
            vlow=vlow,
            vhigh=vhigh,
            strict=strict,
            output_type=output_type,
            mode=mode,
        )
    except Exception as e:
        if not strict:
            logger.warning(f"Worker error for component {component.get('cokey')}: {e}")
            return None
        raise


def _process_parallel(
    components: list[dict],
    var_name: str | list[str] | None,
    target_depths: list[tuple[int, int]],
    lam: float,
    vlow: float,
    vhigh: float,
    n_workers: int | None,
    strict: bool,
    output_type: str,
    mode: str,
) -> list:
    """Process components using multiprocessing."""
    from functools import partial

    harmonized = []

    # Create partial function with fixed arguments
    worker = partial(
        _harmonize_worker,
        var_name=var_name,
        target_depths=target_depths,
        lam=lam,
        vlow=vlow,
        vhigh=vhigh,
        strict=strict,
        output_type=output_type,
        mode=mode,
    )

    with Pool(processes=n_workers) as pool:
        results = pool.imap_unordered(worker, components)

        for i, result in enumerate(results):
            if result is not None:
                harmonized.append(result)

            if (i + 1) % 100 == 0:
                logger.debug(f"Processed {i + 1} components")

    return harmonized


def to_soilprofilecollection(
    harmonized_df: pd.DataFrame,
    idcol: str = "cokey",
    depthcols: tuple[str, str] = ("UD", "LD"),
) -> Any | None:
    """
    Convert harmonized results to SoilProfileCollection format (optional).

    Requires soilprofilecollection package to be installed.

    Args:
        harmonized_df: DataFrame from mpspline()
        idcol: Column name for site/component identifier
        depthcols: Tuple of (upper_depth_col, lower_depth_col) names

    Returns:
        SoilProfileCollection object or None if soilprofilecollection unavailable

    Raises:
        ImportError: If soilprofilecollection is not installed
    """
    if not HAS_SPC:
        raise ImportError(
            "soilprofilecollection is required but not installed. "
            "Install with: pip install mpspline[spc]"
        )

    # Prepare data in SoilProfileCollection format
    # Extract depth columns if present, otherwise use placeholder
    if depthcols[0] in harmonized_df.columns and depthcols[1] in harmonized_df.columns:
        hz_df = harmonized_df.copy()
    else:
        # Create placeholder depths
        hz_df = harmonized_df.copy()
        hz_df[depthcols[0]] = 0
        hz_df[depthcols[1]] = 100

    # Create SoilProfileCollection
    spc = SoilProfileCollection(
        hz_df,
        idname=idcol,
        hzidname="hzname" if "hzname" in hz_df.columns else None,
        depthcols=depthcols,
    )

    return spc
