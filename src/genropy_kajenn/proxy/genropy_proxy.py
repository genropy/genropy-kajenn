# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""GenropyProxyMixin — a genropy legacy db behind an OpenApiApplication.

An ``OpenApiApplication`` mounts a RoutingClass and exposes it as REST (and, via
``McpOpenApiApplication``, as MCP). When those handlers need the genropy legacy
db, someone must own its lifecycle: the connection is thread-local and must be
closed on the thread that opened it — the executor thread where the handler ran,
not the loop. kajenn provides exactly that hook (``route_cleanup``, run in
the executor thread by ``make_callable``); this mixin fills it.

The mixin instantiates a ``GnrApp`` and exposes it as ``self.gnr_app`` (the only
channel the mounted RoutingClass reads, e.g. through its parent). It overrides
only what it owns — ``route_cleanup`` (close the current thread's connection) —
and never the ``OpenApiApplication`` machinery. Direction of dependency is
genropy-kajenn -> kajenn: this imports ``gnr.*``; kajenn never imports genropy.

Compose it with the base to get a mountable app::

    class GenropyProxyOpenApiApplication(GenropyProxyMixin, OpenApiApplication):
        ...
"""

from __future__ import annotations

import logging
from typing import Any

from genro_routes import route

from kajenn import HTTPForbidden, HTTPUnauthorized
from kajenn.applications.openapi import OpenApiApplication

log = logging.getLogger("genropy_kajenn.proxy")

__all__ = ["GenropyProxyMixin", "GenropyProxyOpenApiApplication"]


class GenropyProxyMixin:
    """Owns a ``GnrApp`` and closes its db connection in the executor thread.

    Mixed before an ``OpenApiApplication``: it builds the GnrApp in its own
    ``__init__`` (before delegating to the base, which mounts the RoutingClass),
    exposes it as ``gnr_app``, and fills ``route_cleanup`` to release the
    thread-local db connection after each handler — where it is thread-correct.
    """

    def __init__(self, *, instance: str | None = None, debug: bool = False, **kwargs: Any) -> None:
        """Build the GnrApp, then let the cooperative chain mount the API (D16).

        Args:
            instance: genropy instance name (or path) resolved by GnrApp.
            debug: Passed through to GnrApp.
            **kwargs: Forwarded up the chain (routing_class, module, docs,
                api_name, code, mount, ...).
        """
        from gnr.app.gnrapp import GnrApp

        if not instance:
            raise ValueError("GenropyProxyMixin requires an 'instance'")
        log.info("Creating GnrApp for instance '%s'", instance)
        self._gnr_app = GnrApp(instance, debug=debug)
        log.info("GnrApp '%s' ready", instance)
        super().__init__(**kwargs)  # type: ignore[misc]

    @property
    def gnr_app(self) -> Any:
        """The hosted GnrApp — the only channel the mounted RoutingClass reads."""
        return self._gnr_app

    def route_cleanup(self) -> None:
        """Close the current thread's db connection after the handler.

        The GnrApp opens its connection thread-local, so it must be closed on
        the executor thread that ran the handler. That is exactly when the core
        calls this: ``RoutedApplication`` wraps every SYNC dispatch in a
        ``try/finally`` that runs it on the pool thread the handler just used
        (``routed_application.py``), after the handler returned or raised. An
        async handler never reaches here — it owns its own awaits.
        """
        db = getattr(self._gnr_app, "db", None)
        if db is not None:
            db.closeConnection()

    @route(media_type="application/json", openapi_method="post")
    def authenticate(
        self, credential: str = "", channel: str = "", _request=None
    ) -> dict[str, Any]:
        """Verify a ``Bearer`` credential against ``adm.api_token``.

        The ``authentication_route`` of a channel: kajenn sends the whole
        ``Authorization`` value as ``credential``; the scheme is matched
        case-insensitively, as kajenn's own route does. Answers kajenn's contract
        ``{identity, tags, data, valid_until}``; ``data`` is the
        ``validate_token`` result without ``user``, ``auth_tags`` and
        ``user_record`` (``avatar.data`` travels with every bus call), the
        ``<pkg>_`` keys passed through unchanged. An unknown, inactive or
        expired token, or a scheme other than ``Bearer``, raises
        ``HTTPUnauthorized``. Reachable through the bus only: an HTTP caller
        gets 403.

        FIXED: the answer's shape (kajenn's contract). PROVISIONAL: the
        identity of a group token (its description, else ``unknown`` plus its
        hint) until genropy makes the description mandatory and unique.
        """
        if _request is None or not _request.scope.get("kajenn.kbus"):
            raise HTTPForbidden("this route serves the KajennBus only")
        scheme, _, token = credential.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPUnauthorized("Bearer credential required")
        db = self._gnr_app.db
        tokens = db.table("adm.api_token")
        info = tokens.validate_token(token)
        db.commit()
        if info is None:
            raise HTTPUnauthorized("invalid or expired token")
        record = tokens.record(pkey=info["token_id"]).output("dict")
        expires_ts = record["expires_ts"]
        identity = info.get("user") or info["description"] or f"unknown{record['token_hint'].strip()}"
        return {
            "identity": identity,
            "tags": [tag for tag in (info["auth_tags"] or "").split(",") if tag],
            "data": {key: value for key, value in info.items() if key not in ("user", "auth_tags", "user_record")},
            "valid_until": expires_ts.timestamp() if expires_ts else None,
        }

    def on_shutdown(self) -> None:
        """Release the GnrApp on server stop, then the base."""
        db = getattr(self._gnr_app, "db", None)
        if db is not None:
            db.closeConnection()
        super().on_shutdown()  # type: ignore[misc]


class GenropyProxyOpenApiApplication(GenropyProxyMixin, OpenApiApplication):
    """OpenApiApplication hosting a GnrApp, mountable on an AsgiServer.

    MRO: the mixin owns ``__init__``/``route_cleanup``/``on_shutdown``; the base
    owns the REST + OpenAPI machinery. Mount it like any OpenApiApplication and
    give it an ``instance`` plus a ``routing_class`` (or ``module``).
    """
