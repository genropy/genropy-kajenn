# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""genropy-proxy — genropy legacy db behind an OpenApiApplication.

``GenropyProxyMixin`` hosts a ``GnrApp`` and closes its thread-local db
connection via the ``route_cleanup`` hook (run in the executor thread by
kajenn's ``make_callable``). ``GenropyProxyOpenApiApplication`` composes the
mixin with ``OpenApiApplication``. The only ``gnr.*``-aware piece; everything
REST/OpenAPI comes from kajenn. 

"""

from .genropy_proxy import GenropyProxyMixin, GenropyProxyOpenApiApplication

__all__ = ["GenropyProxyMixin", "GenropyProxyOpenApiApplication"]
__version__ = "0.1.0"
