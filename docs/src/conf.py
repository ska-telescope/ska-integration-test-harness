# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------
import os
import sys
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
sys.path.insert(0, os.path.abspath('../../src'))


# -- Project information -----------------------------------------------------

# General information about the project.
project = 'SKA Integration Test Harness'
copyright = '2024, IDS Srl'
author = 'Emanuele Lena <emanuele.lena@designcoaching.net>'

# The full version, including alpha/beta/rc tags.
version = '0.1.2'

# -- General configuration ------------------------------------------------

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    'm2r',
]

source_suffix = ['.rst', '.md']

# "numpy", "tango",
autodoc_mock_imports = [
    "assertpy", 
    "tango", 
    "ska_control_model", 
    "ska_tango_testing", 
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
    'python': ('https://docs.python.org/3.10', None), 
    'pytest': ("https://docs.pytest.org/en/7.1.x/", None),
    "tango": ("https://pytango.readthedocs.io/en/v9.4.2/", None),
}

def copy_images(app):
    if app.builder.name != 'html':
        return
    
    output_dir = os.path.join(app.outdir, 'uml-docs')
    source_dir = os.path.join(app.srcdir, '..', '..', 'src', 'ska_integration_test_harness', 'uml-docs')

    # create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # list the png files in the source directory
    images = [f for f in os.listdir(source_dir) if f.lower().endswith('.png')]

    # copy the images to the output directory
    for image in images:
        source_path = os.path.join(source_dir, image)
        output_path = os.path.join(output_dir, image)
        with open(source_path, 'rb') as f:
            with open(output_path, 'wb') as out:
                out.write(f.read())

def setup(app):
    # connect the copy_images function to the builder-inited signal
    app.connect('builder-inited', copy_images)


intersphinx_mapping = {
    'python': ('https://docs.python.org/3.10', None), 
    "tango": ("https://pytango.readthedocs.io/en/v9.4.2/", None),
    "ska_tango_testing": ("https://developer.skao.int/projects/ska-tango-testing/en/latest/", None),
}
