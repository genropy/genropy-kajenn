# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""genropy-spa — genropy legacy bridge on the kajenn SPA core.

A :class:`GenropySpaApplication` is the core ``SpaApplication`` whose pool
workers are :class:`~genropy_kajenn.spa.genropy_worker.GenropyWorker` instances,
each hosting a legacy ``GnrWsgiSite`` behind the core's ``wsgi_app`` seam.
The worker side is reached by dotted path (``worker_class``), so importing
this package never requires genropy.
"""

from .genropy_spa_application import GenropySpaApplication

__all__ = ["GenropySpaApplication"]
from importlib.metadata import version as _distribution_version

__version__ = _distribution_version("genropy-kajenn")
