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
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'discord-ui'
copyright = '2021, 404kuso, RedstoneZockt'
author = '404kuso, RedstoneZockt'

def get_version():
    """returns the version of the package"""
    with open("../../discord_ui/__init__.py", "r", encoding="utf-8") as f:
        return [f for f in f.readlines() if f.startswith("__version__")][0].split('"')[1].split('"')[0]

# The full version, including alpha/beta/rc tags
release = get_version()


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx_rtd_theme', 'sphinx_copybutton']
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for copy-button -------------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: |> "
copybutton_prompt_is_regexp = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# def setup(app):
#     app.add_css_file('css/main.css')

# html_context = {
#     'css_files': ['css/main.css'],
#     'js_files': ['js/override_page.js', 'js/keyboard.js'],
# }

def setup(app):
    app.add_css_file('css/main.css')
    app.add_js_file("js/override_page.js")
    app.add_js_file("js/keyboard.js")