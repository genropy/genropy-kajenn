# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Tests for GnrAppWrapperMixin — the db of a genropy legacy instance inside a kajenn application.

The structural/unit tests use a fake GnrApp (an external dependency stub) and run
always: they verify the hooks the mixin owns — ``route_cleanup`` closes the db
connection, ``gnr_app`` exposes the hosted app, and the MRO is correct.

The end-to-end test REQUIRES genropy installed and the ``test_invoice_pg``
instance available; it skips only without genropy or ``psycopg2``. It mounts the
wrapper with a minimal RoutingClass that reads ``application.gnr_app`` and drives a real request,
checking the db connection is closed by ``route_cleanup``.
"""

import importlib.util

import pytest
from genro_routes import RoutingClass, route

from kajenn.routed_application import RoutedApplication
from genropy_kajenn.gnrapp_wrapper import GnrAppWrapperApplication, GnrAppWrapperMixin

_HAS_GNR = importlib.util.find_spec("gnr") is not None
_INSTANCE = "test_invoice_pg"


class _FakeDb:
    """Stub of GnrApp.db: records how many times closeConnection was called."""

    def __init__(self):
        self.closed = 0

    def closeConnection(self):
        self.closed += 1


class _FakeGnrApp:
    """Stub of GnrApp: exposes a db with closeConnection, nothing else."""

    def __init__(self):
        self.db = _FakeDb()


@pytest.fixture
def wrapper(monkeypatch):
    """A GnrAppWrapperApplication whose GnrApp is a stub.

    Patches gnr.app.gnrapp.GnrApp — the external dependency — so no real genropy
    instance is needed. Everything else is the real kajenn machinery.
    """
    import sys
    import types

    fake_module = types.ModuleType("gnr.app.gnrapp")
    fake_module.GnrApp = lambda instance, debug=False: _FakeGnrApp()
    monkeypatch.setitem(sys.modules, "gnr", types.ModuleType("gnr"))
    monkeypatch.setitem(sys.modules, "gnr.app", types.ModuleType("gnr.app"))
    monkeypatch.setitem(sys.modules, "gnr.app.gnrapp", fake_module)
    return GnrAppWrapperApplication(instance=_INSTANCE)


def test_is_openapi_application_subclass():
    assert issubclass(GnrAppWrapperApplication, RoutedApplication)


def test_mixin_comes_before_base_in_mro():
    mro = GnrAppWrapperApplication.__mro__
    assert mro.index(GnrAppWrapperMixin) < mro.index(RoutedApplication)


def test_requires_an_instance(monkeypatch):
    import sys
    import types

    fake_module = types.ModuleType("gnr.app.gnrapp")
    fake_module.GnrApp = lambda instance, debug=False: _FakeGnrApp()
    monkeypatch.setitem(sys.modules, "gnr", types.ModuleType("gnr"))
    monkeypatch.setitem(sys.modules, "gnr.app", types.ModuleType("gnr.app"))
    monkeypatch.setitem(sys.modules, "gnr.app.gnrapp", fake_module)
    with pytest.raises(ValueError):
        GnrAppWrapperApplication()


def test_gnr_app_is_exposed(wrapper):
    assert isinstance(wrapper.gnr_app, _FakeGnrApp)


def test_route_cleanup_closes_connection(wrapper):
    assert wrapper.gnr_app.db.closed == 0
    wrapper.route_cleanup()
    assert wrapper.gnr_app.db.closed == 1


def test_on_shutdown_closes_connection(wrapper):
    wrapper.on_shutdown()
    assert wrapper.gnr_app.db.closed == 1


class _DemoApi(RoutingClass):
    """Minimal RoutingClass that reaches the GnrApp through its parent."""

    def __init__(self, application):
        self.application = application

    @route()
    def whoami(self):
        return type(self.application.gnr_app).__name__


class _DemoApplication(GnrAppWrapperApplication):
    """A wrapper application that attaches the demo routing class under ``api``."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.route.add_branches({"name": "api", "instance": _DemoApi(self)})


@pytest.mark.skipif(not _HAS_GNR, reason="genropy not installed")
def test_e2e_real_gnrapp_closes_connection():
    pytest.importorskip("psycopg2")
    from kajenn import AsgiServer
    from genropy_kajenn.spa.site_engine_factory import GenropySiteEngineFactory

    GenropySiteEngineFactory(source=_INSTANCE, debug=False).build_site()

    server = AsgiServer(
        applications=[(_DemoApplication, {"code": "wrapper", "instance": _INSTANCE})]
    )
    app = server.applications["wrapper"]
    assert app.gnr_app is not None
    assert app.gnr_app.db is not None
    assert app.server is server
    received = _fire_get(app, "/api/whoami")
    assert received["status"] == 200
    app.on_shutdown()


def _fire_get(app, path):
    import asyncio

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "http_version": "1.1",
    }
    received = {"status": None, "body": b""}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            received["status"] = message["status"]
        elif message["type"] == "http.response.body":
            received["body"] += message.get("body", b"")

    asyncio.run(app(scope, receive, send))
    return received
