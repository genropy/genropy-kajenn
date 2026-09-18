CLI reference — ``gnrkajenn``
=============================

``gnrkajenn`` is the ASGI replacement for ``gnrwsgiserve``. It resolves a genropy
instance name to its path, writes what it was given into the environment, and
starts a kajenn ``AsgiServer`` from the built-in recipe — with the pool already
running.

Synopsis
--------

.. code-block:: console

   gnrkajenn [-h] [-H HOST] [-p PORT] [--reload] [--nodebug] [--fulldebug]
             [--config CONFIG]
             instance

Options
-------

The table is the ``argparse`` parser of ``genropy_kajenn/spa/cli.py``, option by
option. Every flag not listed here does not exist.

.. list-table::
   :header-rows: 1
   :widths: 24 16 60

   * - Option
     - Default
     - Description
   * - ``instance``
     - *(required)*
     - genropy instance/site name, or a path to a site directory. An existing
       directory is used as it is, made absolute; anything else is resolved
       through genropy's ``PathResolver.site_name_to_path``. The result is
       written to ``KAJENN_PATH``.
   * - ``-H``, ``--host``
     - ``None``
     - Bind host. Passed unset, the recipe binds ``127.0.0.1``. A value is
       written to ``KAJENN_HOST`` and also handed to ``AsgiServer.serve``.
   * - ``-p``, ``--port``
     - ``None``
     - Listening port. Passed unset, the recipe binds ``8000``. A value is
       written to ``KAJENN_PORT`` and also handed to ``AsgiServer.serve``.
   * - ``--reload``
     - off
     - Accepted for surface compatibility; the core server has no reloader. The
       command prints a line saying the flag was accepted and ignored. Restart to
       pick up code changes.
   * - ``--nodebug``
     - off
     - Turn debug off, by writing the empty string to ``KAJENN_DEBUG``. Debug is
       **on** unless you say otherwise: it brings the SQL time counters and the
       developer's extras.
   * - ``--fulldebug``
     - off
     - Debug **and** the werkzeug debugger: it writes ``KAJENN_DEBUG=1`` and
       ``KAJENN_DEBUGGER=1``. See the warning below.
   * - ``--config CONFIG``
     - *(built-in recipe)*
     - A server ``config.py`` — a ``ServerConfiguration`` — instead of
       ``genropy_kajenn/spa/config.py``. The config carries the pool shape; the
       CLI instance, host and port still win, because they are written to the
       environment before the server is built.

.. warning::

   ``--fulldebug`` adds the werkzeug debugger, whose error page **evaluates
   Python in the process**. Debug alone does not bring it, so that page can never
   appear by accident. Development only.

What the command does before serving
------------------------------------

In this order:

#. ``GNR_DAEMON_PROVIDER`` is set to ``genropy-kajenn`` with ``setdefault`` —
   before anything imports the site machinery, so ``gnr.web.daemon`` resolves to
   the in-process register and never to a daemon client. A value already in the
   environment is left alone.
#. The instance is resolved to a path and written to ``KAJENN_PATH``.
#. Host, port and the debug flags are written to their variables, if given.
#. A ``KAJENN_WORKERS`` found in the environment is reported and ignored.
#. ``AsgiServer`` is built from the config path and ``serve()`` is called.

``Ctrl-C`` prints ``Shutdown.`` and the command returns 0.

What is not there
-----------------

``--workers`` does not exist, and neither does a single/pool selector. The pool
always runs and sizes itself: the number of processes is a reading, never a
setting.

Run from a config file
----------------------

.. code-block:: console

   # through gnrkajenn — the CLI instance/host/port win, the config brings the shape
   $ gnrkajenn mysite --config path/to/pool_config.py -p 8080

   # through the kajenn core CLI — the config supplies everything
   $ kajenn serve path/to/pool_config.py

See :doc:`configuration`.

Remote database, SSL, and the rest
----------------------------------

Site-level launch concerns handled by genropy itself — a remote database over an
SSH tunnel, SSL certificates, a data restore — are configured exactly as with
``gnrwsgiserve``, through the site's own configuration and the genropy
environment. genropy-kajenn changes *how* the site is served, not *what* the site
is.
