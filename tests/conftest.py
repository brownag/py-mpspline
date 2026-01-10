"""
Pytest configuration and fixtures for mpspline tests.

Provides common test data and fixtures for horizon sequence and
component harmonization tests.
"""

import pytest


@pytest.fixture
def simple_horizons() -> list[dict]:
    """Simple 2-horizon sequence for testing."""
    return [
        {
            "hzname": "Ap",
            "upper": 0,
            "lower": 20,
            "clay": 24.5,
            "sand": 42.3,
            "silt": 33.2,
            "om_r": 3.2,
        },
        {
            "hzname": "Bt",
            "upper": 20,
            "lower": 50,
            "clay": 35.2,
            "sand": 28.1,
            "silt": 36.7,
            "om_r": 0.8,
        },
    ]


@pytest.fixture
def miami_soil() -> dict:
    """
    Miami soil series component (Alfisol).

    Representative data for Miami soil, a common soil series used in
    pedometric research and validation.
    """
    return {
        "cokey": 1234567,
        "compname": "Miami",
        "comppct_r": 85,
        "taxorder": "Alfisols",
        "taxsuborder": "Udalfs",
        "horizons": [
            {
                "hzname": "Ap",
                "upper": 0,
                "lower": 20,
                "clay": 24.5,
                "sand": 42.3,
                "silt": 33.2,
                "om_r": 3.2,
                "ph1to1h2o_r": 6.2,
            },
            {
                "hzname": "BA",
                "upper": 20,
                "lower": 30,
                "clay": 28.3,
                "sand": 35.2,
                "silt": 36.5,
                "om_r": 1.5,
                "ph1to1h2o_r": 6.0,
            },
            {
                "hzname": "Bt1",
                "upper": 30,
                "lower": 50,
                "clay": 35.2,
                "sand": 28.1,
                "silt": 36.7,
                "om_r": 0.8,
                "ph1to1h2o_r": 5.8,
            },
            {
                "hzname": "Bt2",
                "upper": 50,
                "lower": 80,
                "clay": 34.8,
                "sand": 30.2,
                "silt": 35.0,
                "om_r": 0.3,
                "ph1to1h2o_r": 5.7,
            },
            {
                "hzname": "BC",
                "upper": 80,
                "lower": 120,
                "clay": 28.5,
                "sand": 38.2,
                "silt": 33.3,
                "om_r": 0.1,
                "ph1to1h2o_r": 5.9,
            },
        ],
    }


@pytest.fixture
def multiple_components(miami_soil: dict) -> list[dict]:
    """Three variations of soil components for bulk processing tests."""
    comp2 = {
        **miami_soil,
        "cokey": 1234568,
        "compname": "Miami taxadjunct",
        "comppct_r": 10,
    }

    comp3 = {
        **miami_soil,
        "cokey": 1234569,
        "compname": "Hennepin",
        "taxorder": "Mollisols",
        "comppct_r": 5,
        "horizons": [
            {
                "hzname": "Ap",
                "upper": 0,
                "lower": 25,
                "clay": 22.0,
                "sand": 45.0,
                "silt": 33.0,
                "om_r": 4.5,
                "ph1to1h2o_r": 6.5,
            },
            {
                "hzname": "AB",
                "upper": 25,
                "lower": 40,
                "clay": 26.0,
                "sand": 40.0,
                "silt": 34.0,
                "om_r": 2.5,
                "ph1to1h2o_r": 6.3,
            },
            {
                "hzname": "Bt",
                "upper": 40,
                "lower": 70,
                "clay": 32.0,
                "sand": 32.0,
                "silt": 36.0,
                "om_r": 0.5,
                "ph1to1h2o_r": 5.8,
            },
        ],
    }

    return [miami_soil, comp2, comp3]


@pytest.fixture
def invalid_horizons_gap() -> list[dict]:
    """Horizons with a gap in depth coverage."""
    return [
        {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
        {"hzname": "Bt", "upper": 30, "lower": 50, "clay": 35.0},  # Gap from 20-30
    ]


@pytest.fixture
def invalid_horizons_overlap() -> list[dict]:
    """Horizons with overlapping depths."""
    return [
        {"hzname": "Ap", "upper": 0, "lower": 25, "clay": 25.0},
        {"hzname": "Bt", "upper": 20, "lower": 50, "clay": 35.0},  # Overlap 20-25
    ]


@pytest.fixture
def invalid_horizons_inverted() -> list[dict]:
    """Horizons with inverted depths."""
    return [
        {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
        {"hzname": "Bt", "upper": 50, "lower": 30, "clay": 35.0},  # Inverted
    ]


@pytest.fixture
def invalid_horizons_missing_field() -> list[dict]:
    """Horizons missing required field."""
    return [
        {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
        {"hzname": "Bt", "lower": 50, "clay": 35.0},  # Missing upper
    ]


@pytest.fixture
def horizon_single() -> list[dict]:
    """Single horizon (below minimum for spline)."""
    return [
        {"hzname": "Ap", "upper": 0, "lower": 20, "clay": 25.0},
    ]
