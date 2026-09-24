# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Worker boundary for WSK calls and the optional live channel checks."""

import asyncio
import io
import os
import re
import unittest

import httpx
from genro_tytx import from_tytx, to_tytx
from kajenn.wsx import WsxEnvelope
from websockets.asyncio.client import connect

from genropy_kajenn.spa.websocket_receiver import WebSocketReceiver


class ReceptionTest(unittest.TestCase):
    def receive(self, payload, page_id="page"):
        def forbidden_dispatch(environ, start_response):
            self.fail("an invalid WSK call must not reach the legacy application")

        receiver = WebSocketReceiver(forbidden_dispatch)
        body = to_tytx(payload, "json").encode()
        environ = {"REQUEST_METHOD": "WSK", "genro.page_id": page_id,
                   "PATH_INFO": "/a/page",
                   "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body)}
        response = []
        chunks = receiver(environ, lambda status, headers: response.append(status))
        return response[0], from_tytx(b"".join(chunks).decode(), "json")

    def test_a_call_that_is_not_an_object_is_refused(self):
        status, result = self.receive([])
        self.assertEqual(status, "400 Bad Request")
        self.assertFalse(result["executed"])

    def test_missing_page(self):
        self.assertEqual(self.receive({"form": "method=probe"}, page_id=None)[0],
                         "400 Bad Request")

    def test_http_is_forwarded_unchanged(self):
        calls = []
        environ = {"REQUEST_METHOD": "POST"}

        def start(status, headers):
            pass

        output = [b"ordinary HTTP"]

        def application(env, callback):
            calls.append((env, callback))
            return output

        self.assertIs(WebSocketReceiver(application)(environ, start), output)
        self.assertEqual(calls, [(environ, start)])


@unittest.skipUnless(os.environ.get("GNR_WSX_TEST_URL"),
                     "set GNR_WSX_TEST_URL for the running test site")
class LiveReceptionTest(unittest.TestCase):
    def test_page_channel_ownership(self):
        base = os.environ["GNR_WSX_TEST_URL"].rstrip("/")
        with httpx.Client(base_url=base, timeout=30) as client:
            page = client.get("/webpages/wsx_rpc")
            page.raise_for_status()
            match = re.search(r"page_id:'([\w-]+)'", page.text)
            self.assertIsNotNone(match)
            page_id = match.group(1)
            cookie = "; ".join(f"{key}={value}" for key, value in client.cookies.items())

        async def exercise():
            async with connect(base.replace("http", "ws", 1) + "/websocket",
                               additional_headers={"Cookie": cookie}, origin=base) as ws:
                async def call(identifier, path, payload, target=page_id):
                    await ws.send(WsxEnvelope(id=identifier, method="WSK", path=path,
                                              page_id=target, data=payload).encode())
                    answer = WsxEnvelope(await asyncio.wait_for(ws.recv(), 10))
                    self.assertEqual(answer.id, identifier)
                    return answer

                rejected = await call("foreign", "/_wsx/openchannel", {}, "not-owned")
                self.assertEqual(rejected.status, 403)
                opened = await call("open", "/_wsx/openchannel",
                                    {"parameters": {"sequential": True}})
                self.assertEqual(opened.status, 200)

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
