# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""gnrapp_wrapper — the db of a genropy legacy instance inside a kajenn application.

``GnrAppWrapperMixin`` hosts a ``GnrApp`` and closes its thread-local db
connection via the ``route_cleanup`` hook (run in the executor thread by
kajenn's ``make_callable``). ``GnrAppWrapperApplication`` composes the mixin
with ``RoutedApplication``. The only ``gnr.*``-aware piece; routing and faces
come from kajenn.
"""

from importlib.metadata import version as _distribution_version

from .gnrapp_wrapper import GnrAppWrapperApplication, GnrAppWrapperMixin

__all__ = ["GnrAppWrapperApplication", "GnrAppWrapperMixin"]
__version__ = _distribution_version("genropy-kajenn")
