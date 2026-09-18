genropy-kajenn documentation
============================

*genropy legacy sites on kajenn: a commander in the server, a supervised pool of
workers each hosting one site, users pinned to a worker, no register daemon.*

**genropy-kajenn** serves an existing, synchronous genropy site on an ASGI
server. One server process holds the front and the commander. Every worker is a
process of its own, hosting one unmodified ``GnrWsgiSite``. A user and all his
pages live in one worker, and every request of his reaches that worker. The site
register — connections, pages, sessions, datachanges, stores — is answered
inside the process that serves the request: there is no register daemon to
start, to connect to or to keep alive.

Your site does not change: same ``root.py``, same packages, same authentication,
same pages. genropy-kajenn changes how the site is served, not what it is.

One command is the whole launch:

.. code-block:: console

   $ gnrkajenn mysite

There is no worker count to declare and no single/pool selector. The pool always
runs, starts with one worker and grows when the workers it has admit nobody.

What it replaces
----------------

* ``gnrwsgiserve`` — the werkzeug/WSGI launcher of the legacy genropy stack.
  ``gnrkajenn`` runs the same site under uvicorn, converting each ASGI request
  to a PEP 3333 environ on a thread pool so the event loop is never blocked.
* ``gnrdaemon`` — the register daemon (Pyro4, then the ``genro-nodaemon`` TCP
  daemon). The register is served in-process, by
  ``genropy_kajenn.siteregister.GenropyRegisterClient``.

What it stands on
-----------------

genropy-kajenn is a bridge, and it owns only the genropy-specific half. Two
distributions carry the rest, and both are installed with it:

* `kajenn <https://kajenn.readthedocs.io/en/latest/>`_ — the ASGI server: the
  listener, the middleware chain, the mounted applications, the configuration
  recipe, the websocket channel.
* `kajenn-orchestra <https://kajenn-orchestra.readthedocs.io/en/latest/>`_ — the
  orchestration: ``SpaApplication`` and its commander, the worker groups, the
  child processes, the freezer on disk, the registers that say who exists and
  where.

The dependency runs one way. ``genropy_kajenn`` imports ``kajenn_orchestra`` and
``kajenn``; neither of them imports genropy, and neither imports this package.
``gnr.*`` is imported by this package alone, and only where a site is hosted.

Where to start
--------------

Read :doc:`concepts` for the model, then :doc:`getting-started` for the launch.
For the whole machine in one page, read :doc:`architecture/overview`.

These pages describe the ``main`` checkout of genropy-kajenn. Source and release
packages may differ; see :doc:`building` for local builds and publication state.

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   getting-started
   concepts

.. toctree::
   :maxdepth: 2
   :caption: Guides

   the-pool
   composition
   single-vs-multi
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/overview

.. toctree::
   :maxdepth: 2
   :caption: Reference

   cli-reference
   configuration
   api

.. toctree::
   :maxdepth: 1
   :caption: FAQ

   faq

.. toctree::
   :maxdepth: 1
   :caption: Building

   building

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
