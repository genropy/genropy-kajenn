Getting started
===============

By the end of this page an existing genropy site is served over ASGI, with no
register daemon, and you know how to check that it is running.

What you need first
-------------------

genropy-kajenn serves a site; it does not create one. A **real genropy instance
is required**, and everything below assumes you already have one working under
``gnrwsgiserve``.

* **Python** >= 3.11.
* **A working genropy environment** — ``~/.gnr/environment.xml`` exists and
  points at your genropy setup, the same file ``gnrwsgiserve`` reads.
* **An existing site** — the same instance name you pass to ``gnrwsgiserve``, or
  the path of a site directory.
* **genropy itself**, installed in the same environment. It is a **runtime**
  requirement: the worker builds a ``GnrWsgiSite`` and imports ``gnr.*`` when it
  runs. It is deliberately not a declared dependency of this package, so
  ``pip install genropy-kajenn`` does not install it.
* **A database driver**, if the site needs one — the driver the site already
  uses under ``gnrwsgiserve``.

.. note::

   **On macOS export** ``PGGSSENCMODE=disable``. The workers of a group are born
   by ``fork`` out of a template process, and libpq negotiating Kerberos inside a
   forked child crashes it. The end-to-end test of this repository sets it for
   the same reason.

Install it
----------

.. code-block:: console

   $ pip install genropy-kajenn

``kajenn`` and ``kajenn-orchestra`` are installed with it. That gives you the
``gnrkajenn`` command and the ``gnr.web:daemon`` entry point — the in-process
register. There is nothing else to configure and no daemon to start.

The entry point is **not** picked up on its own. genropy replaces its daemon
namespace only when ``GNR_DAEMON_PROVIDER`` names a provider, and ``gnrkajenn``
writes that variable for its own process before anything imports the site
machinery. The consequence is worth knowing: the classic stack and this one can
share one virtualenv, because the choice is per process.

To follow current development, take the three packages from GitHub:

.. code-block:: console

   $ pip install git+https://github.com/kajenn-org/kajenn.git
   $ pip install git+https://github.com/kajenn-org/kajenn-orchestra.git
   $ pip install git+https://github.com/genropy/genropy-kajenn.git

From a checkout, for development:

.. code-block:: console

   $ pip install -e ".[dev]"

Read the command
----------------

.. code-block:: console

   $ gnrkajenn --help
   usage: gnrkajenn [-h] [-H HOST] [-p PORT] [--reload] [--nodebug] [--fulldebug]
                    [--config CONFIG]
                    instance

   positional arguments:
     instance         genropy instance/site name (or path)

   options:
     -h, --help       show this help message and exit
     -H, --host HOST
     -p, --port PORT
     --reload         accepted for surface compatibility; the core server has no
                      reloader
     --nodebug
     --fulldebug      debug AND the werkzeug debugger: the error page with a
                      traceback and a console that evaluates Python in the
                      process. Debug alone gives the SQL counters and the
                      developer's extras without that page
     --config CONFIG  server config.py (a ServerConfiguration) instead of the
                      built-in recipe; the config carries the pool shape while
                      the CLI instance still wins

Every option is described in :doc:`cli-reference`.

Serve your site
---------------

.. code-block:: console

   $ gnrkajenn mysite

``mysite`` is the genropy instance name — the same you pass to ``gnrwsgiserve`` —
or a path to a site directory. A name is resolved through genropy's own
``PathResolver``; an existing directory is used as it is.

Without ``-H`` and ``-p`` the recipe binds ``127.0.0.1`` on port ``8000``, so the
site answers on ``http://127.0.0.1:8000/``. What the terminal prints while it
comes up is uvicorn's own startup logging plus the site's; this page does not
transcribe it, because it depends on the site and on your logging configuration.

Change host and port:

.. code-block:: console

   $ gnrkajenn mysite -p 9000                # a different port
   $ gnrkajenn mysite -H 0.0.0.0 -p 9000     # host and port

Turn debug off:

.. code-block:: console

   $ gnrkajenn mysite --nodebug

.. note::

   ``--reload`` is accepted for surface compatibility with ``gnrwsgiserve`` and
   then ignored: the command prints a line saying so. Restart the process to pick
   up code changes.

There is no ``--workers``. The pool always runs and sizes itself: it starts with
one worker and another is born when none of the living ones admits a newcomer. A
``KAJENN_WORKERS`` still set in the environment is reported on startup and
ignored. See :doc:`the-pool`.

Check that it runs
------------------

Open ``http://<host>:<port>/`` in a browser. The site behaves as it does under
``gnrwsgiserve``.

Read the site-wide counters — no authentication, because the built-in recipe
mounts no authentication at all:

.. code-block:: console

   $ curl -s http://127.0.0.1:8000/metrics

The answer is Prometheus exposition text. The population family is the one the
legacy ``/metrics`` webtool exposes, kept identical so an existing scrape
configuration keeps working, and it is followed by the commander's own event
counters:

.. code-block:: text

   genropy_site_counters{counter="users"} 2
   genropy_site_counters{counter="pages"} 2
   genropy_site_counters{counter="connections"} 2
   genropy_site_events{event="requests_refused"} 0

The three population numbers are the exact sizes of the commander's own indexes —
the whole pool's view, not one worker's. The ``genropy_site_events`` family is
the commander's aggregate counters, and a counter appears only once it has been
incremented, so the lines that follow depend on what the pool has done.

Next steps
----------

* :doc:`concepts` — the model in words: commander, pool, pinning, the register.
* :doc:`architecture/overview` — the same thing in four diagrams.
* :doc:`the-pool` — how the pool grows, where a user lives, what happens when he
  goes quiet.
* :doc:`cli-reference` — every ``gnrkajenn`` option.
* :doc:`configuration` — the environment variables, and when a config file of
  your own earns its place.
* :doc:`composition` — a REST surface, an MCP endpoint or an async app beside the
  site.
