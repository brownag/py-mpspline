Quick Start
===========

5-Minute Quick Start
--------------------

Import and use mpspline in just a few lines:

.. code-block:: python

    from mpspline import mpspline

    # Define a single soil profile
    profile = {
        'horizons': [
            {'hzname': 'A', 'upper': 0, 'lower': 20, 'clay': 24.5},
            {'hzname': 'B', 'upper': 20, 'lower': 50, 'clay': 35.2},
        ]
    }

    # Harmonize to standard depths
    result = mpspline(profile, var_name=['clay'])

    # Access harmonized values
    print(result['clay_0_5'])    # Clay % at 0-5 cm
    print(result['clay_5_15'])   # Clay % at 5-15 cm
    print(result['clay_15_30'])  # Clay % at 15-30 cm

Single Profile Processing
--------------------------

Process a single profile and get a dictionary with harmonized values:

.. code-block:: python

    from mpspline import mpspline

    component = {
        'cokey': 12345,
        'compname': 'Miami',
        'horizons': [
            {
                'hzname': 'Ap',
                'upper': 0,
                'lower': 20,
                'clay': 24.5,
                'sand': 42.3,
                'silt': 33.2,
            },
            {
                'hzname': 'Bt',
                'upper': 20,
                'lower': 50,
                'clay': 35.2,
                'sand': 28.1,
                'silt': 36.7,
            },
        ]
    }

    # Harmonize clay, sand, silt to GlobalSoilMap depths
    result = mpspline(component, var_name=['clay', 'sand', 'silt'])

    # Result includes original metadata + harmonized values
    print(result['cokey'])          # 12345 (preserved)
    print(result['compname'])       # 'Miami' (preserved)
    print(result['clay_0_5'])       # Harmonized clay at 0-5 cm
    print(result['sand_5_15'])      # Harmonized sand at 5-15 cm

Batch Processing
----------------

Process multiple profiles efficiently:

.. code-block:: python

    from mpspline import mpspline
    import pandas as pd

    profiles = [
        {
            'cokey': 1,
            'horizons': [
                {'upper': 0, 'lower': 20, 'clay': 20},
                {'upper': 20, 'lower': 50, 'clay': 30},
            ]
        },
        {
            'cokey': 2,
            'horizons': [
                {'upper': 0, 'lower': 15, 'clay': 22},
                {'upper': 15, 'lower': 45, 'clay': 32},
            ]
        },
    ]

    # Returns a pandas DataFrame
    df = mpspline(profiles, var_name=['clay'])

    print(df)
    #    cokey  clay_0_5  clay_5_15  clay_15_30  ...
    # 0      1     20.50      20.75       24.50  ...
    # 1      2     22.00      21.50       26.50  ...

Default Depth Intervals
-----------------------

By default, mpspline uses GlobalSoilMap standard depths:

- 0-5 cm (topsoil/organic interface)
- 5-15 cm (topsoil)
- 15-30 cm (upper subsoil)
- 30-60 cm (mid-subsoil)
- 60-100 cm (deep subsoil)
- 100-200 cm (very deep/C-horizon)

Custom depths are also supported (see :doc:`parameters`).

Horizon Input Format
--------------------

Each horizon should contain:

- **Top depth** (required): Can be named `upper`, `top`, `start`, `depth_min`, or `hzdept_r`
- **Bottom depth** (required): Can be named `lower`, `bottom`, `end`, `depth_max`, or `hzdepb_r`
- **Horizon name** (optional): Can be named `hzname`, `name`, or `label`
- **Properties** (required): Any numeric fields to harmonize (clay, sand, silt, etc.)

Example:

.. code-block:: python

    horizon = {
        'hzname': 'Ap',           # Optional
        'upper': 0,               # Required (depth to top)
        'lower': 20,              # Required (depth to bottom)
        'clay': 24.5,             # Property 1
        'sand': 42.3,             # Property 2
        'silt': 33.2,             # Property 3
    }

Next Steps
----------

- **Parameters**: Learn about tuning lambda, constraints, and more - see :doc:`parameters`
- **Performance**: Speed up large processing jobs - see :doc:`performance`
- **Troubleshooting**: Common issues and solutions - see :doc:`troubleshooting`
- **Examples**: More detailed examples in the `examples/` directory
- **API Reference**: Full function documentation - see :doc:`api`
