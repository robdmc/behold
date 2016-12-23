# -*- coding: utf-8 -*-
#
import inspect
import os
import re
import sys

file_dir = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(file_dir, '..'))

def get_version():
    """Obtain the packge version from a python file e.g. pkg/__init__.py
    See <https://packaging.python.org/en/latest/single_source_version.html>.
    """
    file_dir = os.path.realpath(os.path.dirname(__file__))
    with open(
            os.path.join(file_dir, '..', 'behold', 'version.py')) as f:
        txt = f.read()
    version_match = re.search(
        r"""^__version__ = ['"]([^'"]*)['"]""", txt, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    #'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    #'sphinxcontrib.fulltoc',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'toc'

# General information about the project.
project = 'behold'
copyright = '2015, Ambition Inc.'

# The short X.Y version.
version = get_version()
# The full version, including alpha/beta/rc tags.
release = version

exclude_patterns = ['_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

intersphinx_mapping = {
    'python': ('http://docs.python.org/3.4', None),
    'django': ('http://django.readthedocs.org/en/latest/', None),
    #'celery': ('http://celery.readthedocs.org/en/latest/', None),
}

# -- Options for HTML output ----------------------------------------------

html_theme = 'default'
#html_theme_path = []

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']
html_static_path = []

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

# Output file base name for HTML help builder.
htmlhelp_basename = 'beholddoc'


## -- Options for LaTeX output ---------------------------------------------
#
#latex_elements = {
# #The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',
#
# #The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',
#
# #Additional stuff for the LaTeX preamble.
#'preamble': '',
#}
#
## Grouping the document tree into LaTeX files. List of tuples
## (source start file, target name, title,
##  author, documentclass [howto, manual, or own class]).
#latex_documents = [
#  ('index', 'behold.tex', 'behold Documentation',
#   'Rob deCarvalho', 'manual'),
#]
#
## -- Options for manual page output ---------------------------------------
#
## One entry per manual page. List of tuples
## (source start file, name, description, authors, manual section).
#man_pages = [
#    ('index', 'behold', 'behold Documentation',
#     ['Rob deCarvalho'], 1)
#]
#
## -- Options for Texinfo output -------------------------------------------
#
## Grouping the document tree into Texinfo files. List of tuples
## (source start file, target name, title, author,
##  dir menu entry, description, category)
#texinfo_documents = [
#  ('index', 'behold', 'behold Documentation',
#   'Rob deCarvalho', 'behold', 'A short description',
#   'Miscellaneous'),
#]
