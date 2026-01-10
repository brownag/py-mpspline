# Configuration file for Sphinx documentation builder.

import os
import sys
import doctest

# Add parent directory to path so we can import mpspline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Project information
project = 'mpspline'
copyright = '2025, Andrew Brown and Lauren O\'Brien'
author = 'Andrew Brown and Lauren O\'Brien'

# The version info
import mpspline
version = mpspline.__version__
release = version

# Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.doctest',
]

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True,
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}

# Theme
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
}

# HTML output
html_static_path = []
html_title = f'{project} {version}'

# Source settings
source_suffix = {'.rst': 'restructuredtext'}
master_doc = 'index'

# Matplotlib settings
plot_include_source = True

# LaTeX output
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '11pt',
}

# Doctest settings
doctest_default_flags = (
    doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.SKIP
)
