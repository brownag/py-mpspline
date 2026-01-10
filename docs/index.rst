mpspline Documentation
======================

Mass-preserving equal-area quadratic splines for harmonizing soil component profiles to standardized depth intervals.

**mpspline** is a Python implementation of mass-preserving spline functions for soil data depth harmonization, based on the `mpspline2 <https://github.com/obrl-soil/mpspline2>`_ R package by Lauren O'Brien.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   parameters
   performance
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api

.. toctree::
   :maxdepth: 2
   :caption: Background

   algorithm

Quick Links
-----------

- `GitHub Repository <https://github.com/brownag/mpspline>`_
- `Bug Tracker <https://github.com/brownag/mpspline/issues>`_
- `Read the README <https://github.com/brownag/mpspline/blob/main/README.md>`_

Key Features
------------

- **Data-agnostic**: Works with dictionaries, lists, or pandas DataFrames
- **Flexible input**: Automatically recognizes common horizon depth column names
- **Mass-preserving**: Maintains average property values across depth intervals
- **Bulk processing**: Efficiently handle hundreds or thousands of profiles
- **Parallel processing**: Optional multiprocessing for large datasets
- **Customizable**: Adjust smoothing parameters, depth intervals, and constraints
- **Well-documented**: Full docstrings and extensive type hints

Basic Usage
-----------

.. code-block:: python

    from mpspline import mpspline

    # Single profile (dict) or multiple profiles (list of dicts)
    result = mpspline({
        'horizons': [
            {'hzname': 'A', 'upper': 0, 'lower': 20, 'clay': 24.5},
            {'hzname': 'B', 'upper': 20, 'lower': 50, 'clay': 35.2},
        ]
    })

    print(result)  # Returns harmonized values at standard depths

References
----------

Bishop, T.F.A., McBratney, A.B., & Laslett, G.M. (1999). Modelling soil attribute depth functions with equal-area quadratic smoothing splines. *Geoderma*, 89(3-4), 185-208. https://doi.org/10.1016/S0016-7061(99)00003-8

Malone, B.P., McBratney, A.B., & Minasny, B. (2009). Mapping continuous depth functions of soil carbon storage and available water capacity. *Geoderma*, 154(3-4), 138-152. https://doi.org/10.1016/j.geoderma.2009.10.007

License
-------

GPL 3.0 - See `LICENSE <https://github.com/brownag/mpspline/blob/main/LICENSE>`_ for details.
