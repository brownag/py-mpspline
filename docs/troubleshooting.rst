Troubleshooting & FAQ
====================

Common issues and solutions.

Installation Issues
-------------------

**Q: ImportError: No module named 'mpspline'**

A: Make sure mpspline is installed:

.. code-block:: bash

    pip install mpspline

Or verify installation:

.. code-block:: bash

    pip list | grep mpspline

**Q: ModuleNotFoundError when importing**

A: You may have multiple Python environments. Check you're using the right one:

.. code-block:: bash

    which python  # See which Python is active
    python -m pip install mpspline

**Q: Version conflicts with dependencies**

A: Install in a clean virtual environment:

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate
    pip install mpspline

Data Input Issues
-----------------

**Q: KeyError: 'horizons'**

A: Your input doesn't have a `'horizons'` key. The correct structure is:

.. code-block:: python

    # ✗ Wrong - no 'horizons' key
    data = {'cokey': 123, 'clay': 25}

    # ✓ Correct - has 'horizons' key
    data = {
        'cokey': 123,
        'horizons': [
            {'upper': 0, 'lower': 20, 'clay': 25}
        ]
    }

**Q: KeyError: 'upper' or 'lower'**

A: Your horizons don't have recognized depth fields. Use one of these names:

.. code-block:: python

    # These all work:
    {'upper': 0, 'lower': 20}      # Recommended
    {'top': 0, 'bottom': 20}
    {'start': 0, 'end': 20}
    {'depth_min': 0, 'depth_max': 20}
    {'hzdept_r': 0, 'hzdepb_r': 20}  # SSURGO standard

    # This does NOT work:
    {'depth': 0, 'lower': 20}      # 'depth' not recognized

**Q: ValueError: Horizons must be ordered by depth**

A: Your horizons have gaps, overlaps, or invalid depths. Check that:

.. code-block:: python

    # ✗ Wrong - overlapping
    {'upper': 0, 'lower': 30}
    {'upper': 20, 'lower': 50}

    # ✓ Correct - sequential
    {'upper': 0, 'lower': 20}
    {'upper': 20, 'lower': 50}

    # ✗ Wrong - inverted
    {'upper': 20, 'lower': 10}

    # ✓ Correct - ordered
    {'upper': 10, 'lower': 20}

**Q: TypeError: unhashable type: 'dict'**

A: You may have passed a single profile incorrectly. For a single profile, pass it directly (not in a list):

.. code-block:: python

    # ✓ Correct - single profile (dict)
    result = mpspline(profile)

    # ✗ Don't pass single profile in list
    result = mpspline([profile])  # Returns DataFrame, not dict

Output Issues
-------------

**Q: Output contains NaN values**

A: This usually happens when the profile doesn't extend to those depths:

.. code-block:: python

    # Profile only goes to 80cm
    profile = {
        'horizons': [
            {'upper': 0, 'lower': 20, 'clay': 20},
            {'upper': 20, 'lower': 80, 'clay': 30},  # Stops at 80cm
        ]
    }

    result = mpspline(profile)
    # Result will have NaN for 100-200cm because profile doesn't go that deep

Solution: Either extend your profile or use custom depths:

.. code-block:: python

    # Option 1: Only use depths your profile covers
    result = mpspline(
        profile,
        target_depths=[(0, 5), (5, 15), (15, 30), (30, 60), (60, 80)]
    )

    # Option 2: Extend profile with lower horizon
    profile['horizons'].append({
        'upper': 80,
        'lower': 120,
        'clay': 28,
    })

**Q: Predicted values seem unrealistic**

A: You may need to add value constraints:

.. code-block:: python

    # ✗ Without constraints, clay might go above 100%
    result = mpspline(profile)

    # ✓ With constraints
    result = mpspline(
        profile,
        var_name=['clay'],
        vlow=0.0,
        vhigh=100.0
    )

**Q: Some properties missing from output**

A: Non-numeric properties are skipped. Check that your properties are numbers:

.. code-block:: python

    horizon = {
        'upper': 0,
        'lower': 20,
        'clay': 25.0,           # ✓ Numeric - included
        'texture': 'loam',      # ✗ String - skipped
        'sand': '40.0',         # ? String number - may or may not work
    }

Solution: Convert to numeric or specify in `var_name`:

.. code-block:: python

    # Option 1: Ensure numeric
    horizon['sand'] = float(horizon['sand'])

    # Option 2: Specify what to process
    result = mpspline(profile, var_name=['clay', 'sand'])

Processing Issues
-----------------

**Q: Processing is very slow**

A: Enable parallel processing and optimize batch size:

.. code-block:: python

    # Enable parallel processing
    df = mpspline(
        profiles,
        parallel=True,      # Use multiple cores
        batch_size=500,     # Tune batch size
        var_name=['clay'],  # Process only needed properties
    )

**Q: Memory error with large dataset**

A: Reduce batch size or use parallel processing:

.. code-block:: python

    # Smaller batches = less memory
    df = mpspline(
        profiles,
        batch_size=50,      # Reduce from default 100
        parallel=False,     # Single process
    )

**Q: Parallel processing doesn't work on Windows**

A: Wrap your code in `if __name__ == '__main__':`:

.. code-block:: python

    from mpspline import mpspline

    if __name__ == '__main__':
        df = mpspline(profiles, parallel=True)

**Q: Getting errors like "RuntimeError: An attempt has been made..."**

A: This usually means the above issue on Windows. Use the if __name__ pattern.

Validation Errors
-----------------

**Q: What does "strict mode" mean?**

A:

.. code-block:: python

    # Lenient mode (default, strict=False)
    # Logs warnings, skips bad profiles, returns results for valid ones
    df = mpspline(profiles, strict=False)

    # Strict mode (strict=True)
    # Raises exception on first error
    df = mpspline(profiles, strict=True)

Use strict=True when debugging, strict=False for production.

**Q: How do I see validation warnings?**

A: Configure Python logging:

.. code-block:: python

    import logging
    logging.basicConfig(level=logging.WARNING)

    result = mpspline(profile, strict=False)

Advanced Issues
---------------

**Q: Why are results slightly different between runs?**

A: Due to floating-point arithmetic, tiny differences (~0.001%) are normal.

**Q: How do I compare results with the R mpspline2?**

A: Results should be nearly identical (within 0.01%). Small differences are due to:
- Python vs R numerical differences
- Different random seeds if parallel
- Rounding differences in display

**Q: What's the meaning of the 'lam' parameter?**

A: It's the smoothing parameter in the spline algorithm. See :doc:`parameters` for details.

Still Having Issues?
--------------------

If you've tried the above solutions:

1. Check the full documentation: https://py-mpspline.readthedocs.io
2. Review the examples in the `examples/` directory
3. Look at the docstrings: `help(mpspline.mpspline)`
4. Open an issue on GitHub: https://github.com/brownag/mpspline/issues

When reporting an issue, please include:
- Python version: `python --version`
- mpspline version: `python -c "import mpspline; print(mpspline.__version__)"`
- Minimal code that reproduces the issue
- Full error message and traceback
