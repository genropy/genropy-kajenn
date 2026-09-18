FAQ
===

What is genropy-kajenn, in one sentence?
   The way to serve an existing genropy site on an ASGI server instead of WSGI,
   with no register daemon, across a supervised pool of worker processes each
   hosting one site.

Do I have to change my site?
   No. The ``GnrWsgiSite`` runs unmodified: same ``root.py``, same packages, same
   authentication, same sessions. genropy-kajenn changes how the site is served,
   not what it is.

How is this different from ``gnrwsgiserve``?
   ``gnrwsgiserve`` runs the site under werkzeug, in one process. ``gnrkajenn``
   runs it under uvicorn, converting each ASGI request to a PEP 3333 environ on a
   thread pool, so the site code stays synchronous and the event loop is never
   blocked. What you gain is the worker pool with its per-user pinning, and no
   register daemon. The command line is the same shape: a site name and a port.

Do I have to choose single or pool?
   No. There is one shape: the pool always runs. It starts with one worker and
   another is born when none of the living ones admits a newcomer, so a small
   site behaves like a single process and a busy one spreads out on its own.
   ``--workers`` does not exist. See :doc:`single-vs-multi`.

What happened to the register daemon?
   It is gone. Historically the site register was a separate process reached over
   a wire — ``gnrdaemon`` with Pyro4, then the ``genro-nodaemon`` TCP daemon.
   genropy-kajenn serves the register **in-process**: there is nothing to start
   or connect to. The package declares the ``gnr.web:daemon`` entry point, and
   genropy installs it as ``gnr.web.daemon`` when ``GNR_DAEMON_PROVIDER`` names
   it — which the CLI does for its own process. So the classic stack and this one
   can share one virtualenv.

Does a user always land on the same worker?
   Yes, while he has a worker. The routing cookie is ``spa_connection_id``, and
   it carries the connection id the site itself created — nothing is minted by
   the front. The commander turns that id into an identity and sends every
   request of his to the worker that holds him, so his in-process state stays
   coherent. He changes worker only through the freezer: he goes quiet, his state
   is written to disk, and his next request wakes him wherever there is room.

How does the pool decide to grow?
   A newcomer is offered to the living workers, fullest first, and each judges
   itself on its own last measurement and refuses by raising — over its setpoint,
   or already holding as many users as it may. One more worker is born only when
   nobody admitted him and the group's memory quota affords it; the newcomer
   waits for that birth. The decision is measured occupancy, not a head count.
   The policy is kajenn-orchestra's, and its documentation describes every
   threshold.

Can I tune when the pool grows?
   The lever the environment exposes is ``KAJENN_WORKER_MAX_USERS``: how many
   users one worker may hold before it refuses the next. Unset, one worker takes
   everybody and a small site never grows a second one. The occupancy setpoints
   and the memory cascade live on the group, reachable through a ``--config``
   recipe. See :doc:`configuration`.

Is shared global state consistent across workers?
   Yes, and not by replication: **there is no replica**. The legacy
   ``globalStore()`` is one dictionary living on the commander, behind one FIFO
   lock. A worker reads it with a call and writes through a grant that lands all
   at once. A subpath write holds a keyed read-modify-write turn, so a sibling
   leaf another worker wrote is never dropped, and a ``with globalStore()`` block
   holds the whole dictionary for its thread and publishes it once on the exit. A
   value that looks stale is a value nobody has written yet.

Does it need genropy at build time?
   No. genropy is a **runtime** requirement: the worker builds a ``GnrWsgiSite``
   and imports ``gnr.*`` when it runs. It is deliberately not a declared
   dependency, so ``pip install genropy-kajenn`` does not bring it — install it
   yourself. The declared dependencies are ``kajenn`` and ``kajenn-orchestra``.

Can I add other apps beside the site?
   Yes. The server is multi-application: declare a REST/OpenAPI surface, an MCP
   endpoint or a native async application in the recipe, each on its own mount,
   all on the same origin and able to reach the same genropy database. Because it
   is one origin, a legacy page can call a new endpoint directly — shared
   cookies, no CORS. See :doc:`composition`.

Where do I see what the pool is doing?
   ``GET /metrics``, unauthenticated, served by the front: the three population
   counters under the legacy metric name ``genropy_site_counters``, then the
   commander's aggregate event counters under ``genropy_site_events``. That is
   the whole observation surface the built-in recipe exposes. kajenn's
   ``_server`` application, monitor included, is not part of that recipe: a
   server that declares no ``_server`` application exposes no ``/_server/...``.
   For the questions nobody predicted, ``KAJENN_CONSOLE`` mounts the pool's debug
   door on ``_console`` — full ``eval``, never in production.

Which user is on which worker?
   That lives in the commander and is readable through the console door. It is
   not published as a page.

Is it faster than ``gnrwsgiserve``?
   **No performance comparison between the two stacks has been produced**, and
   none should be inferred from these pages. The repository carries a comparison
   bench — recorders on both stacks, a replay that stops at the first divergence,
   a twin proxy that performs each request on both — and its purpose so far has
   been fidelity, not speed. Measurements taken while the two stacks ran in
   different execution modes may not be quoted.

What state is this package in?
   Version 0.1.0, classified ``Development Status :: 3 - Alpha`` in
   ``pyproject.toml``. The serving path, the register, the data plane and the
   fork-born workers have dedicated tests; the launch recipe and the CLI are
   exercised by running the command, not by the suite. The modules of the old
   daemon surface — ``handler.py``, ``service.py``, ``processes.py`` — exist only
   so the imports resolve and raise when used.

   .. admonition:: Under review
      :class: warning

      The distribution is ``0.1.0`` but ``genropy_kajenn.__init__`` carries
      ``__version__ = "0.8.0"``, and ``genropy_kajenn.spa`` carries
      ``__version__ = "0.6.0"``. They are the predecessor's numbers. This
      documentation reads the version from the installed distribution metadata
      and never from those attributes.
