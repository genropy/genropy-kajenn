# Copyright 2026 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""The authentication route of GenropyProxyMixin, end to end on test_invoice_pg.

Each test mounts a GenropyProxyOpenApiApplication on a real kajenn server,
configures a channel whose ``authentication_route`` is the proxy's
``authenticate`` route, and sends a request carrying ``Authorization: Bearer``
to a route that returns what the handler sees of its avatar. Tokens and the
user are created through ``adm.api_token`` / ``adm.user`` and deleted after.
"""

import asyncio
import importlib.util
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

from genro_tytx import from_tytx

from kajenn import AsgiServer
from kajenn.asgi_endpoint import BufferedAsgiEndpoint

pytestmark = pytest.mark.skipif(importlib.util.find_spec("gnr") is None, reason="genropy not installed")

RECIPE = '''
from genro_routes import route

from kajenn import RoutedApplication
from kajenn.config.templates import CONFIGURATION_TEMPLATES
from genropy_kajenn.proxy import GenropyProxyOpenApiApplication


class Echo(RoutedApplication):
    @route()
    def avatar(self, _request=None):
        avatar = _request.avatar()
        return {"identity": avatar.identity, "tags": sorted(avatar.tags),
                "data": avatar.data.as_dict(recursive=True)}


class Recipe(CONFIGURATION_TEMPLATES["default"]):
    def applications_section(self, cfg):
        apps = cfg.applications()
        apps.application(code="proxy", app_class=GenropyProxyOpenApiApplication,
                         instance="test_invoice_pg")
        apps.application(code="echo", app_class=Echo)
        cfg.channels().channel(name="rest", authentication_route="/proxy/authenticate")
'''


@asynccontextmanager
async def running(tmp_path):
    path = tmp_path / "config.py"
    path.write_text(RECIPE)
    server = AsgiServer(config=str(path))
    inbox: asyncio.Queue = asyncio.Queue()
    outbox: asyncio.Queue = asyncio.Queue()
    lifespan = asyncio.create_task(server(
        {"type": "lifespan", "asgi": {"version": "3.0"}}, inbox.get, outbox.put))
    await inbox.put({"type": "lifespan.startup"})
    assert (await outbox.get())["type"] == "lifespan.startup.complete"
    try:
        yield server
    finally:
        await inbox.put({"type": "lifespan.shutdown"})
        await outbox.get()
        await lifespan


async def call(server, path, *, method="GET", authorization=None, tytx=False):
    headers = [(b"authorization", authorization.encode())] if authorization else []
    if tytx:
        headers.append((b"x-tytx-transport", b"json"))
    result = await BufferedAsgiEndpoint(server).serve({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
        "root_path": "", "query_string": b"", "headers": headers,
        "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 80),
    }, b"")
    return result["status"], dict(result["headers"]), result["body"]


async def avatar_of(server, token):
    status, _, body = await call(server, "/echo/avatar", authorization=f"Bearer {token}", tytx=True)
    assert status == 200, body
    return from_tytx(body.decode(), "json")


class Rows:
    """The adm rows one test creates through the proxy's db, deleted after."""

    def __init__(self, db):
        self.db = db
        self.users = []
        self.tokens = []
        self.tags = []

    def tag(self, code):
        """The tag ``code``, created when the database does not have it (a fresh one has none)."""
        table = self.db.table("adm.htag")
        found = table.query(where="$code=:c", c=code).fetch()
        if found:
            return found[0]["pkey"]
        record = table.newrecord(code=code, description=code)
        table.insert(record)
        self.tags.append(record["id"])
        return record["id"]

    def user(self, username, tags=()):
        table = self.db.table("adm.user")
        record = table.newrecord(username=username, status="conf", firstname="Kj", lastname="Test")
        table.insert(record)
        for code in tags:
            self.db.table("adm.user_tag").insert(dict(user_id=record["id"], tag_id=self.tag(code)))
        self.db.commit()
        self.users.append(record["id"])
        return record["id"]

    def token(self, description=None, user_id=None, tags=(), expires_ts=None):
        table = self.db.table("adm.api_token")
        record = table.newrecord(description=description, user_id=user_id, expires_ts=expires_ts)
        table.insert(record)
        for code in tags:
            self.db.table("adm.api_token_tag").insert(dict(api_token_id=record["id"], tag_id=self.tag(code)))
        value = table.activate_api_token(record["id"])
        self.db.commit()
        self.tokens.append(record["id"])
        return record["id"], value

    def read_token(self, token_id):
        self.db.closeConnection()
        return self.db.table("adm.api_token").record(pkey=token_id).output("dict")

    def delete(self):
        for table, pkeys in (("adm.api_token", self.tokens), ("adm.user", self.users), ("adm.htag", self.tags)):
            if pkeys:
                self.db.table(table).deleteSelection(where="$id IN :pkeys", pkeys=pkeys)
        self.db.commit()
        self.db.closeConnection()


@pytest.fixture
async def live(tmp_path):
    async with running(tmp_path) as server:
        rows = Rows(server.applications["proxy"].gnr_app.db)
        try:
            yield server, rows
        finally:
            rows.delete()


async def test_a_group_token_authenticates_as_its_description(live):
    # wf:contract: a token with no user_id and description "ci-client" yields an
    # wf:contract: avatar whose identity is "ci-client" and whose tags are the
    # wf:contract: token's auth_tags split on commas
    server, rows = live
    _, value = rows.token(description="ci-client", tags=("user",))
    avatar = await avatar_of(server, value)
    assert avatar["identity"] == "ci-client"
    assert avatar["tags"] == ["user"]


async def test_a_group_token_without_description_authenticates_as_unknown_with_its_hint(live):
    # wf:contract: a token with no user_id and an empty description yields the
    # wf:contract: identity "unknown" followed by the token's token_hint
    # wf:contract: ("..." and the last four characters of the token value)
    server, rows = live
    _, value = rows.token(description="")
    avatar = await avatar_of(server, value)
    assert avatar["identity"] == f"unknown...{value[-4:]}"


async def test_a_user_token_authenticates_as_its_user_with_the_users_tags(live):
    # wf:contract: a token with a user_id yields the identity of the user's
    # wf:contract: username and tags holding both the user's tags and the token's
    server, rows = live
    user_id = rows.user("kjtest_user_tags", tags=("admin",))
    _, value = rows.token(description="user token", user_id=user_id, tags=("user",))
    avatar = await avatar_of(server, value)
    assert avatar["identity"] == "kjtest_user_tags"
    assert {"admin", "user"} <= set(avatar["tags"])


async def test_data_carries_the_validation_result_with_package_keys(live):
    # wf:contract: avatar.data holds token_id, group_code and description of the
    # wf:contract: validate_token result, and for a user token user_id and
    # wf:contract: user_name too; the result's "user" and "auth_tags" are not in it
    server, rows = live
    group_token_id, group_value = rows.token(description="ci-client")
    user_id = rows.user("kjtest_user_data")
    user_token_id, user_value = rows.token(description="user token", user_id=user_id)
    group_data = (await avatar_of(server, group_value))["data"]
    user_data = (await avatar_of(server, user_value))["data"]
    assert group_data["token_id"] == group_token_id
    assert "group_code" in group_data
    assert group_data["description"] == "ci-client"
    assert user_data["token_id"] == user_token_id
    assert "group_code" in user_data
    assert user_data["description"] == "user token"
    assert user_data["user_id"] == user_id
    assert user_data["user_name"] == "Kj Test"
    for data in (group_data, user_data):
        assert "user" not in data
        assert "auth_tags" not in data
    assert "user_record" not in user_data


async def test_a_token_with_two_tags_authenticates_with_both(live):
    server, rows = live
    _, value = rows.token(description="two-tags", tags=("admin", "user"))
    avatar = await avatar_of(server, value)
    assert avatar["tags"] == ["admin", "user"]


async def test_the_scheme_is_matched_case_insensitively(live):
    server, rows = live
    _, value = rows.token(description="ci-client", tags=("user",))
    status, _, _ = await call(server, "/echo/avatar", authorization=f"bearer {value}", tytx=True)
    assert status == 200


async def test_the_route_reports_the_tokens_expiry_as_valid_until(live):
    # wf:contract: called over the bus, the route answers valid_until equal to the
    # wf:contract: token's expires_ts as a POSIX timestamp, and None for a token
    # wf:contract: with no expires_ts
    server, rows = live
    expiring_id, expiring = rows.token(description="expiring",
                                       expires_ts=datetime.now(timezone.utc) + timedelta(days=1))
    _, lasting = rows.token(description="lasting")
    expires_ts = rows.read_token(expiring_id)["expires_ts"]
    answer = await server.kbus_call("/proxy/authenticate", {"credential": f"Bearer {expiring}", "channel": "rest"})
    assert answer["valid_until"] == expires_ts.timestamp()
    answer = await server.kbus_call("/proxy/authenticate", {"credential": f"Bearer {lasting}", "channel": "rest"})
    assert answer["valid_until"] is None


async def test_an_invalid_or_expired_token_is_a_401_to_the_client(live):
    # wf:contract: an unknown token value, a token whose expires_ts is past, and
    # wf:contract: an Authorization header with a scheme other than Bearer all
    # wf:contract: give the client status 401 with the WWW-Authenticate Bearer challenge
    server, rows = live
    _, expired = rows.token(description="expired", expires_ts=datetime.now(timezone.utc) - timedelta(days=1))
    for authorization in ("Bearer not-a-token", f"Bearer {expired}", f"Basic {expired}"):
        status, headers, _ = await call(server, "/echo/avatar", authorization=authorization)
        assert status == 401, authorization
        assert headers["www-authenticate"].startswith("Bearer"), authorization


async def test_the_route_refuses_an_http_caller(live):
    # wf:contract: a plain HTTP request to the authenticate route gets 403
    server, _ = live
    status, _, _ = await call(server, "/proxy/authenticate", method="POST")
    assert status == 403


async def test_a_validation_records_the_tokens_last_use(live):
    # wf:contract: after one authenticated request the token's last_used_ts is set
    server, rows = live
    token_id, value = rows.token(description="ci-client")
    assert rows.read_token(token_id)["last_used_ts"] is None
    await avatar_of(server, value)
    assert rows.read_token(token_id)["last_used_ts"] is not None
