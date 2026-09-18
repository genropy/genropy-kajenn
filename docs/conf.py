# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Sphinx configuration for the genropy-kajenn documentation."""

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

# The package is expected to be installed (``pip install -e ".[docs]"``); add
# ``src`` to the path as a fallback so autodoc resolves imports either way.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

project = "genropy-kajenn"
copyright = "2025-2026, Softwell S.r.l."
author = "Genropy Team"
# The DISTRIBUTION version, read from the installed metadata. The import
# package also carries a ``__version__``, and the two do not agree: the
# documentation quotes this one.
try:
    release = _pkg_version("genropy-kajenn")
except PackageNotFoundError:
    release = "0.0.0.dev0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
# ``internal`` holds working notes marked DA REVISIONARE, two of them in
# Italian; ``verification`` holds the logs of live acceptance sessions. Neither
# is user documentation and neither is built.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "internal", "verification"]

# MyST: the narrative pages are Markdown; the toctree skeleton and the
# reference pages are rst.
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
myst_heading_anchors = 3
# ``:::{admonition}`` is a colon fence; without this extension MyST prints the
# fence as text instead of building the directive.
myst_enable_extensions = ["colon_fence"]
# A ```mermaid fence in Markdown is handed to the ``mermaid`` directive.
myst_fence_as_directive = ["mermaid"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["readability.css"]
html_title = f"genropy-kajenn {release}"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Napoleon: the codebase uses Google-style docstrings.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
# ``__init__`` docstrings are NOT merged into the class. This codebase opens
# them with ``Args:`` on the summary line itself, which Napoleon does not read
# as a section: docutils then sees an unexpected indentation and the build
# fails. The constructor kwargs of the classes a recipe names are described in
# the configuration guide instead.
napoleon_include_init_with_doc = False

# Autodoc mocks ``gnr`` and nothing else. genropy is a runtime requirement and
# not a declared dependency, so it is absent wherever this documentation is
# built; ``kajenn`` and ``kajenn_orchestra`` are declared dependencies and are
# really installed. Mocking ``kajenn`` while ``kajenn_orchestra`` is real puts a
# mock in the base chain of the classes documented here, and autodoc's walk over
# that chain does not terminate: that is what timed out the Read the Docs build
# of commit e9d9cf7 at the 15-minute limit.
autodoc_mock_imports = ["gnr"]
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}

# Compact diagrams share the documentation palette and use readable labels.
mermaid_light_theme = "base"
mermaid_dark_theme = "base"
mermaid_init_config = {
    "startOnLoad": False,
    "theme": "base",
    "themeVariables": {
        "fontFamily": "Arial, sans-serif",
        "fontSize": "16px",
        "primaryColor": "#FFF8E8",
        "primaryTextColor": "#24262B",
        "primaryBorderColor": "#AD7410",
        "lineColor": "#526174",
        "secondaryColor": "#EDF1F5",
        "tertiaryColor": "#FFFFFF",
    },
    "flowchart": {"nodeSpacing": 24, "rankSpacing": 28, "useMaxWidth": False},
}

mermaid_width = "auto"
mermaid_height = "auto"
