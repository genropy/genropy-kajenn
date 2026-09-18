Add more apps beside the site
=============================

Serve a REST/OpenAPI surface, an MCP endpoint or a native async app next to the
legacy site — one process, one port, one origin, the same genropy database.

Applications are declared, never mounted
----------------------------------------

``AsgiServer`` builds every application from its configuration. There is no
``mount`` method and no application instance to hand over: you write a recipe, a
subclass of kajenn's ``AsgiConfigBuilder``, and name the class and its kwargs
there. ``gnrkajenn --config path/to/recipe.py`` runs it.

Start from ``genropy_kajenn/spa/config.py`` — the recipe every default launch
uses — and add to it. Reading it is the shortest answer to any question this page
does not cover.

Two ways to grow
----------------

* **Beside** — declare separate applications, each on its own mount (``api``,
  ``mcp``, …). The site keeps the root; the new applications answer on first path
  segments the site never used.
* **In place** — add native routes to the front itself, on paths the site already
  owns, so they shadow the legacy handler one path at a time.

Beside: a REST / OpenAPI surface on the site's database
-------------------------------------------------------

``GenropyProxyOpenApiApplication`` (from ``genropy_kajenn.proxy``) hosts a
``GnrApp`` behind kajenn's ``OpenApiApplication``. Your routing class exposes
plain methods as REST; the mixin closes the thread-local database connection on
the executor thread after each handler, which is where it is thread-correct.
Point it at the same instance the site serves:

.. code-block:: python

   from kajenn.config import AsgiConfigBuilder

   from genropy_kajenn.proxy import GenropyProxyOpenApiApplication
   from genropy_kajenn.spa.genropy_spa_application import GenropySpaApplication


   class ServerConfiguration(AsgiConfigBuilder):
       def main(self, root):
           cfg = root.configuration()
           cfg.server(host="127.0.0.1", port=8000)
           cfg.middleware()
           applications = cfg.applications()
           applications.application(code="api", mount="api",
                                    app_class=GenropyProxyOpenApiApplication,
                                    instance="mysite",      # the genropy instance
                                    module="myproject.api",  # the routing class
                                    docs="swagger")
           # ... the site front and its orchestration node, as in spa/config.py

``instance`` is required: the mixin raises ``ValueError`` without one. Supply the
API either as ``routing_class=`` (an instance) or as ``module=`` (a dotted path
the application imports). The mounted class is attached under ``api_name``, which
defaults to ``api``, so a method named ``customers`` answers on
``/api/api/customers``; set ``api_name`` to change that segment. The OpenAPI meta
endpoints sit under ``_meta`` — ``/api/_meta/`` — in every case.

Beside: the same class as MCP
-----------------------------

``McpOpenApiApplication`` (from ``kajenn.applications.mcp``) is
``OpenApiApplication`` plus an MCP face over the very same router: one set of
methods serves a REST client and an agent, with no second implementation.

.. code-block:: python

   from kajenn.applications.mcp import McpOpenApiApplication

   applications.application(code="tools", mount="tools",
                            app_class=McpOpenApiApplication,
                            module="myproject.api")

The MCP JSON-RPC face answers under ``mcp_name_segment``, which defaults to
``mcp`` — so ``/tools/mcp``. Which methods are visible there is the ``channel``
plugin's job: the MCP face lists only entries declared on channel ``mcp``, and a
method that declares nothing stays REST-only.

That class has no genropy database of its own. To expose a genropy database as
MCP, compose ``GenropyProxyMixin`` with it the way
``GenropyProxyOpenApiApplication`` composes it with ``OpenApiApplication``: the
mixin comes first, so it owns ``__init__``, ``route_cleanup`` and
``on_shutdown``, and the base keeps its own machinery.

In place: replace site paths one at a time
------------------------------------------

The front demultiplexes in two stages. Stage one reads the first segment of the
path: not one of the application's own first-level roots, and the path belongs to
the hosted site. Stage two resolves the full path in the application's own
router: the node exists, so the request is served natively; a structural miss
under a claimed root falls through to the site after all.

Claiming a root therefore does **not** claim its whole subtree. A single native
route shadows exactly its own path, and the site keeps serving every sibling.

.. code-block:: python

   from genro_routes import route

   from genropy_kajenn.spa.genropy_spa_application import GenropySpaApplication


   class MySite(GenropySpaApplication):
       @route(media_type="application/json")
       def sys_health(self):
           return {"status": "ok"}

Then name ``MySite`` as the ``app_class`` of the site application in the recipe.
It is the same seam ``GenropySpaApplication`` itself uses for ``metrics``. Move
the stateless service paths first; paths that need the legacy page context —
session, avatar, rendered state — are the last to move.

.. note::

   This is the shape of the strangler fig migration: the new system grows around
   the old and replaces it gradually, with a working system at every step.
   Nothing forces it — it is what the two-stage demux makes possible.

One origin
----------

Every application lives under one host and port, so the browser sees one origin:
no CORS to configure, and the legacy session cookie is sent to every path. A
legacy genropy page can reach a new endpoint directly — a ``fetch("/api/…")``
from page code, or an ``<iframe>`` embedding a modern view inside the classic UI.

The framework injects nothing into legacy pages. You embed from the legacy side,
pointing at the declared mount.

Where the extra applications run
--------------------------------

They run in the **server process**, beside the front — not in the workers. The
front forwards to the workers only what belongs to the hosted site: every path
whose first segment is not one of its own roots. An application declared on its
own mount is a different first segment, so it is served locally. Each keeps its
own ``GnrApp`` and closes its database connection on the thread that used it,
independently of the workers hosting the site.
