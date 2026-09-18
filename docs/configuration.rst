Configuration
=============

For an ordinary site there is nothing to configure. ``gnrkajenn mysite`` builds a
complete server from a fixed recipe — ``genropy_kajenn/spa/config.py`` — whose
only variable elements come from the environment.

This page lists those variables, describes what the recipe builds, and says when
a config file of your own earns its place.

Environment variables
---------------------

Every variable below is read by the built-in recipe or written by the CLI.
Nothing else is read.

.. list-table::
   :header-rows: 1
   :widths: 30 12 58

   * - Variable
     - Type
     - Default and effect
   * - ``KAJENN_PATH``
     - path
     - No default. The resolved site path. The CLI writes it from the
       ``instance`` argument **before** the server is built, so a ``--config``
       recipe that reads it serves the instance named on the command line. The
       built-in recipe derives from it the site key, the freezer path and the
       socket directory.
   * - ``KAJENN_HOST``
     - string
     - ``127.0.0.1``. The bind address. Written by ``-H``.
   * - ``KAJENN_PORT``
     - integer
     - ``8000``. The listening port. Written by ``-p``.
   * - ``KAJENN_DEBUG``
     - word
     - **Unset means on.** A value is read as a word: ``""``, ``0``, ``false``,
       ``no`` and ``off`` mean off, anything else means on. Debug builds the site
       in debug mode — the SQL time counters, the developer's extras.
       ``--nodebug`` writes the empty string.
   * - ``KAJENN_DEBUGGER``
     - any value
     - Unset. Any value wraps the site in the werkzeug debugger, whose error page
       carries a traceback and a console that evaluates Python in the process.
       Written by ``--fulldebug``, and never on as a side effect of debug.
   * - ``KAJENN_FROZEN_USERS_PATH``
     - path
     - ``<site>/data/_frozen_users``. The freezer root. It defaults **inside** the
       site's own ``data`` directory because a frozen user is kept for days and
       that directory survives.
   * - ``KAJENN_INSTANCE_DIR``
     - path
     - ``<system temp>/gnrkajenn_<site key>``. Where the workers' unix sockets live.
       Ephemeral, and under the temp directory because a unix socket path has to
       stay short.
   * - ``KAJENN_IDLE_FREEZE_MINUTES``
     - float
     - Unset. The silence past which a user is parked in the freezer. Unset, the
       worker reads the site's own ``<cleanup>`` section
       (``connection_max_age``, in seconds), and 7200 seconds where the site says
       nothing.
   * - ``KAJENN_WORKER_MAX_USERS``
     - integer
     - Unset. How many users one worker may hold before it refuses the next.
       Unset, kajenn-orchestra's own default governs — unlimited — so on a small
       site one worker takes everybody and the pool never grows.
   * - ``KAJENN_CONSOLE``
     - any value
     - Unset. Any value mounts the pool's debug door on ``_console`` as MCP
       tools. Full ``eval``: mounting **is** the gate. Never in production.
   * - ``KAJENN_ORCHESTRATION_PROFILES``
     - any value
     - Unset. Any value mounts the orchestration profile archive on ``_sysop``.
       It stores named JSON profiles and applies nothing to the running pool. The
       mount is unauthenticated: see the warning below.
   * - ``KAJENN_ORCHESTRATION_PROFILES_PATH``
     - path
     - ``<site>/data/_orchestration_profiles``. Where those profiles live.
   * - ``GNR_DAEMON_PROVIDER``
     - string
     - No default. The CLI writes ``genropy-kajenn`` before the site machinery is
       imported. It is what makes genropy resolve its ``gnr.web.daemon``
       namespace to the in-process register. Set it yourself only when you build
       the server without the CLI.
   * - ``KAJENN_WORKERS``
     - —
     - **No longer read.** The CLI prints a line when it finds it set, and
       ignores it: the worker count is a reading, never a setting.

.. note::

   ``KAJENN_WORKER_MAX_USERS=1`` puts every user on a worker of his own. That is
   how the cross-worker paths — the register population, the stores, the changes
   travelling between users — get exercised at all, so it is the value a test
   bench wants and not one a production site needs.

What the built-in recipe builds
-------------------------------

Without a config file, ``gnrkajenn`` builds:

* the listener, from ``KAJENN_HOST`` and ``KAJENN_PORT``;
* the middleware chain;
* **one** ``GenropySpaApplication``, code ``site``, mounted on the **root**. A
  genropy site owns its absolute URLs — ``/_rsrc``, ``/sys``, the dojo tree — so
  it cannot live under a prefix, and a non-empty mount is refused at
  construction;
* under that front, an ``orchestration`` node with one commander, carrying the
  freezer path and the socket directory;
* under that commander, **one** group named ``pool``: its ``worker_class`` is
  ``genropy_kajenn.spa.genropy_worker:GenropyWorker``, its ``engine_factory`` is
  ``genropy_kajenn.spa.site_engine_factory:GenropySiteEngineFactory`` (which is
  what makes its workers forks of a template process), and its
  ``worker_kwargs`` carry the site source and the two debug flags;
* ``cpu_retirement_quiet_seconds=60.0`` on that group, written explicitly. Every
  other threshold is kajenn-orchestra's own default.

What it does **not** build: no authentication, no session middleware in front of
the site — both stay inside the ``GnrWsgiSite`` — and no ``_server``
application, so there is no ``/_server/...`` surface at all.

The recipe is ``genropy_kajenn/spa/config.py``, and reading it is the shortest
answer to any question this page does not cover.

.. _orchestration-profiles:

The orchestration profile archive
---------------------------------

Set ``KAJENN_ORCHESTRATION_PROFILES`` and the recipe mounts kajenn-orchestra's
``ConfigurationProfilesApplication`` on ``_sysop``:

.. code-block:: console

   $ KAJENN_ORCHESTRATION_PROFILES=1 gnrkajenn mysite

The archive **stores** named JSON profiles in a directory of the site. It knows
nothing about the orchestration runtime and touches nothing that is running.

Surfaces:

* an editor page and the REST API below ``/_sysop/configuration``, with the
  operations ``profiles`` (list), ``read``, ``save`` (POST, a JSON object body)
  and ``delete`` (DELETE);
* the same four operations as MCP tools at ``/_sysop/mcp``.

A profile is one ``<name>.json`` file. The name is 1 to 64 characters — letters,
digits, dot, dash or underscore — and the ``.json`` suffix may be given or
omitted. The content must be a JSON object of at most 1 MiB, and a write is
atomic. What a profile may carry is kajenn-orchestra's group grammar; its own
documentation lists the keys.

.. warning::

   The mount is **unauthenticated**: whoever reaches the port can read and write
   profiles. It is opt-in for that reason — development and lab only. Before
   production the sysop surface must be gated.

When a config file earns its place
----------------------------------

Reach for ``--config`` when you need something the recipe does not declare: a
second application beside the site (see :doc:`composition`), the ``_server``
application and an administrator for it, or group settings the environment does
not expose — the memory cascade, the occupancy setpoints, more than one group.

A config file is a ``ServerConfiguration``, a subclass of kajenn's
``AsgiConfigBuilder``. Start from ``genropy_kajenn/spa/config.py`` and change
what you need: it is a working recipe, not an example.

.. code-block:: console

   $ gnrkajenn mysite --config path/to/my_config.py -p 8081

The CLI writes the instance, host and port into the environment before the server
is built, so a recipe reading ``KAJENN_PATH`` serves the instance you named.
