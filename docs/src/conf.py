# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys


sys.path.insert(0, os.path.abspath("../../src"))


# -- Project information -----------------------------------------------------

# General information about the project.
project = "SKA Integration Test Harness"
copyright = "2024, IDS Srl"
author = "Emanuele Lena <emanuele.lena@designcoaching.net>"

# The full version, including alpha/beta/rc tags.
version = "0.4.0"

# -- General configuration ------------------------------------------------

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints", 
]

source_suffix = [".rst", ".md"]

# "numpy", "tango",
autodoc_mock_imports = [
    "assertpy",
    "tango",
    "ska_control_model",
    "ska_tango_testing",
    "pydantic",
]


# Add any paths that contain templates here, relative to this directory.
# templates_path = []

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "ska_ser_sphinx_theme"

html_context = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = []


intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10", None),
    "pytest": ("https://docs.pytest.org/en/7.1.x/", None),
    "tango": ("https://pytango.readthedocs.io/en/v9.4.2/", None),
    "ska_tango_testing": (
        "https://developer.skao.int/projects/ska-tango-testing/en/latest/",
        None,
    ),
    "ska_control_model": (
        "https://developer.skao.int/projects/ska-control-model/en/latest/",
        None,
    ),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
