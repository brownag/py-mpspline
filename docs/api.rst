API Reference
=============

Complete API documentation for mpspline.

Main Function
-------------

.. autofunction:: mpspline.spline.mpspline
   :members:

Classes
-------

HorizonSequence
~~~~~~~~~~~~~~~

.. autoclass:: mpspline.spline.HorizonSequence
   :members:
   :undoc-members:

ValidationResult
~~~~~~~~~~~~~~~~

.. autoclass:: mpspline.validation.ValidationResult
   :members:

Secondary Functions
-------------------

Single Profile Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: mpspline.spline.mpspline_one
   :members:

Algorithm Functions
~~~~~~~~~~~~~~~~~~~

.. autofunction:: mpspline.algorithm.spline_one
   :members:

.. autofunction:: mpspline.algorithm.spline_multiple
   :members:

Validation
~~~~~~~~~~

.. autofunction:: mpspline.validation.validate_horizon_sequence
   :members:

Constants
---------

Standard Depths
~~~~~~~~~~~~~~~

.. autodata:: mpspline.constants.GLOBALSM_DEPTHS

Standard Soil Properties
~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: mpspline.constants.STANDARD_SOIL_PROPERTIES

Spline Tolerance
~~~~~~~~~~~~~~~~

.. autodata:: mpspline.constants.SPLINE_TOLERANCE

Module Index
------------

.. toctree::
   :maxdepth: 1

.. autosummary::
   :toctree: _autosummary

   mpspline.spline
   mpspline.algorithm
   mpspline.validation
   mpspline.constants
   mpspline.utils
