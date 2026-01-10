Parameters
==========

Complete reference for mpspline() parameters.

Function Signature
------------------

.. code-block:: python

    mpspline(
        obj: Union[Dict, List[Dict]],
        var_name: Union[str, List[str]] = None,
        target_depths: Optional[List[Tuple[int, int]]] = None,
        lam: float = 0.1,
        vlow: float = 0.0,
        vhigh: float = 1000.0,
        batch_size: int = 100,
        parallel: bool = False,
        n_workers: Optional[int] = None,
        strict: bool = False,
    ) -> Union[Dict, pd.DataFrame]

Parameters
----------

**obj** : dict or list of dict
    Input data.

    - Single profile (dict): Returns dict with harmonized values
    - Multiple profiles (list of dicts): Returns pandas DataFrame

    Each profile must have a `'horizons'` key with list of horizon dicts.

**var_name** : str, list of str, or None
    Property/properties to harmonize.

    - `None` (default): Harmonizes all numeric fields found in horizons
    - `'clay'`: Harmonizes only clay
    - `['clay', 'sand']`: Harmonizes clay and sand

    Numeric string values will be converted to floats. Non-numeric fields are skipped.

**target_depths** : list of tuples or None
    Depth intervals as `(top, bottom)` in cm.

    Default: GlobalSoilMap standard depths

    .. code-block:: python

        [(0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200)]

    Can be customized for your analysis:

    .. code-block:: python

        # Shallow sampling
        target_depths = [(0, 5), (5, 10), (10, 20), (20, 40)]

        # Deep profile
        target_depths = [(0, 10), (10, 30), (30, 60), (60, 100), (100, 200)]

**lam** : float
    Smoothing parameter (default: 0.1)

    Controls how closely the spline fits the original data:

    - **0.01** (high smoothing): Smooth predictions, tolerates noisy data
    - **0.1** (medium smoothing, default): Balanced fit between smoothness and data fit
    - **1.0** (low smoothing): Closer to original data points

    Try different values based on your data quality. Example:

    .. code-block:: python

        # For noisy data
        result = mpspline(profile, lam=0.01)

        # For accurate data
        result = mpspline(profile, lam=1.0)

**vlow** : float
    Minimum constraint for predictions (default: 0.0)

    Prevents unrealistic low values. For example:

    .. code-block:: python

        # Clay percentage cannot be negative
        result = mpspline(profile, var_name=['clay'], vlow=0.0)

        # Bulk density is typically > 1 g/cm³
        result = mpspline(profile, var_name=['bdensity'], vlow=1.0)

**vhigh** : float
    Maximum constraint for predictions (default: 1000.0)

    Prevents unrealistic high values. For example:

    .. code-block:: python

        # Clay percentage cannot exceed 100%
        result = mpspline(profile, var_name=['clay'], vhigh=100.0)

        # Bulk density typically < 2 g/cm³
        result = mpspline(profile, var_name=['bdensity'], vhigh=2.0)

**batch_size** : int
    Number of profiles per batch (default: 100)

    Only applies when processing multiple profiles. Used for memory optimization.
    For very large datasets, reduce batch size to lower memory usage:

    .. code-block:: python

        # For memory-constrained systems
        df = mpspline(large_profile_list, batch_size=50)

**parallel** : bool
    Enable multiprocessing (default: False)

    Only applies when processing multiple profiles (list input).
    Speeds up processing on multi-core systems:

    .. code-block:: python

        # Use all available CPU cores
        df = mpspline(profiles, parallel=True)

**n_workers** : int or None
    Number of worker processes (default: None = CPU count)

    Only applies when `parallel=True`. Limit CPU usage:

    .. code-block:: python

        # Use only 2 cores
        df = mpspline(profiles, parallel=True, n_workers=2)

**strict** : bool
    Error handling mode (default: False)

    - **False** (lenient): Log warnings and skip problematic profiles/properties
    - **True**: Raise exceptions on validation errors

    Example:

    .. code-block:: python

        # Lenient mode: skip bad profiles, return results for valid ones
        df = mpspline(profiles, strict=False)

        # Strict mode: fail fast on first error
        try:
            df = mpspline(profiles, strict=True)
        except ValueError as e:
            print(f"Validation error: {e}")

Common Parameter Combinations
------------------------------

**Single profile, basic usage:**

.. code-block:: python

    result = mpspline(profile, var_name=['clay', 'sand'])

**Multiple profiles, all properties:**

.. code-block:: python

    df = mpspline(profiles)

**Multiple profiles with constraints:**

.. code-block:: python

    df = mpspline(
        profiles,
        var_name=['clay', 'sand'],
        vlow=0.0,
        vhigh=100.0
    )

**Large dataset with parallel processing:**

.. code-block:: python

    df = mpspline(
        profiles,
        var_name=['clay'],
        parallel=True,
        batch_size=500,
        lam=0.1
    )

**Custom depths for research project:**

.. code-block:: python

    custom_depths = [(0, 5), (5, 25), (25, 50), (50, 100)]
    result = mpspline(
        profile,
        target_depths=custom_depths,
        var_name=['clay', 'sand', 'silt']
    )

Horizon Input Format
--------------------

Flexible depth field names (all recognized):

.. code-block:: python

    # All of these work:
    {'upper': 0, 'lower': 20}
    {'top': 0, 'bottom': 20}
    {'start': 0, 'end': 20}
    {'depth_min': 0, 'depth_max': 20}
    {'hzdept_r': 0, 'hzdepb_r': 20}

Property fields (any numeric field):

.. code-block:: python

    {
        'upper': 0,
        'lower': 20,
        'clay': 24.5,           # Will be harmonized
        'sand': 42.3,           # Will be harmonized
        'silt': 33.2,           # Will be harmonized
        'texture': 'loam',      # Skipped (non-numeric)
        'color': 'brown',       # Skipped (non-numeric)
    }
