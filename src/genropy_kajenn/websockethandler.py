# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""The websocket handler genropy builds as ``site.wsk`` when the bridge is selected.

genropy's ``gnr.web.gnrwsgisite_proxy.gnrwebsockethandler.websocketHandlerClass``
resolves the ``gnr.web`` entry point ``websockethandler`` when
``GNR_DAEMON_PROVIDER`` is set, the same variable that already selects the
register provider. A provider that declares no such entry point keeps genropy's
own handler, so the register can be replaced without the socket.
``genropy_kajenn.spa.cli`` sets the variable to ``genropy-kajenn``, the
distribution name this package publishes, and this module is what the entry
point names. Without the variable genropy keeps its own class
and this module is never loaded.

What genropy consumes, and nothing else:

``WsgiWebSocketHandler``
    the class the entry point points at. genropy's selector rejects anything that
    is not a class carrying callable ``checkSocket`` and ``sendCommandToPage``.

``WsgiWebSocketHandler(site)``
    one positional argument, the ``GnrWsgiSite``. ``GnrWsgiSite.wsk`` builds it.

``checkSocket()``
    ``True`` keeps the handler as ``site.wsk``; ``False`` turns ``site.websockets``
    off for the life of the process. There is no ``async.sock`` to probe: the
    answer is the operator's switch ``KAJENN_WEBSOCKET``, which ``gnrkajenn
    --websocket`` writes. Unset, the socket is off and every page call travels
    over HTTP (decision of 2026-10-15: after a restart that forgot the page, the
    ``gnrwebsocket_kajenn`` client retries without end, while the HTTP road shows
    genropy's own reload notice).

``sendCommandToPage(page_id, command, data)``
    the page's one outbound call. ``GnrWebPage._register_new_page`` sends
    ``('', 'registerNewPage', Bag(...))`` on every new page. Pages are ephemeral
    here, so nothing is registered and nothing is delivered: the call returns
    ``None``. Server-to-page delivery is outside the WSK scope.

``client_module``
    the javascript module name that replaces ``gnrwebsocket`` in the frontend
    imports. ``gnrwebsocket_kajenn`` is the name of the client genropy ships for
    this contract; it opens the page channel, pings, and sends correlated WSK
    calls. A handler without the attribute leaves the frontend imports
    untouched.

``setInClientData``, ``fireInClientData`` and ``publishToClient`` are part of
genropy's own handler and are not part of this contract: a page reaches them only
through ``wsk_enabled`` push paths, which stay on the pull road.
"""

import os

# The operator's switch: any value turns the page socket on.
WEBSOCKET_ENV = "KAJENN_WEBSOCKET"


class WsgiWebSocketHandler:
    """The websocket handler of a site served by the bridge."""

    client_module = "gnrwebsocket_kajenn"

    def __init__(self, site):
        self.site = site

    def checkSocket(self):
        """Report the socket as available only when ``KAJENN_WEBSOCKET`` carries a value."""
        return bool(os.environ.get(WEBSOCKET_ENV))

    def sendCommandToPage(self, page_id, command, data):
        """Drop the command: the websocket carries page rpc, not server-to-page delivery."""
        pass
