Installation
=============

PyPI Installation
-----------------

The easiest way to install mpspline is using pip:

.. code-block:: bash

    pip install mpspline

This installs the stable release with all required dependencies (numpy, pandas, scipy).

Development Installation
-------------------------

To install from source for development:

.. code-block:: bash

    git clone https://github.com/brownag/mpspline.git
    cd mpspline
    pip install -e ".[dev]"

This installs the package in editable mode with development dependencies (pytest, ruff, mypy, etc.).

Optional Dependencies
---------------------

Some optional features require additional packages:

.. code-block:: bash

    # For SoilProfileCollection integration
    pip install -e ".[spc]"

    # For documentation building
    pip install -e ".[docs]"

    # All extras (dev + spc + docs)
    pip install -e ".[dev,spc,docs]"

System Requirements
-------------------

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows
- **Dependencies**:
  - numpy >= 1.20.0
  - pandas >= 1.3.0
  - scipy >= 1.7.0

Troubleshooting Installation
-----------------------------

**ImportError: No module named 'mpspline'**

Make sure mpspline is installed:

.. code-block:: bash

    pip list | grep mpspline
    pip install mpspline

**Version conflicts**

If you encounter dependency version conflicts, try installing in a fresh virtual environment:

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install mpspline

**Build errors on Windows**

Make sure you have a C compiler installed. If you see errors like "error: Microsoft Visual C++ 14.0 is required", install the Visual C++ build tools from Microsoft.

Verifying Installation
----------------------

Test that mpspline is correctly installed:

.. code-block:: python

    >>> import mpspline
    >>> print(mpspline.__version__)
    0.1.0

Or run the quick test:

.. code-block:: bash

    python -c "from mpspline import mpspline; print('mpspline is installed!')"
