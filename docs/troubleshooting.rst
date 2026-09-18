Troubleshooting
===============

Symptom, cause, fix.

Startup
-------

**"the following arguments are required: instance"**
   You passed no instance. ``gnrkajenn`` takes one, always: ``gnrkajenn mysite``.

**The instance name does not resolve**
   A name that is not an existing directory goes through genropy's
   ``PathResolver.site_name_to_path``, the same resolution ``gnrwsgiserve`` uses.
   If it fails, the site is not where genropy looks. Pass the site directory path
   instead and the resolver is skipped.

**genropy environment not found**
   genropy-kajenn runs an existing, configured genropy site. ``~/.gnr/environment.xml``
   must exist and point at your genropy environment — the same setup
   ``gnrwsgiserve`` needs.

**``ModuleNotFoundError: gnr``**
   genropy is not installed in this environment. It is a runtime requirement and
   deliberately not a declared dependency, so ``pip install genropy-kajenn`` does
   not bring it.

**The recipe names no site**
   The front refuses to start with ``group <name>: worker_kwargs names no
   source``. A group whose workers host no site would come up and refuse every
   request, so the defect is said at boot. It only happens with a ``--config``
   recipe of your own: declare
   ``worker_kwargs={"source": <site name or path>}``.

**A worker dies on macOS as soon as it is forked**
   Export ``PGGSSENCMODE=disable``. Workers are born by ``fork`` out of a
   template process, and libpq negotiating Kerberos inside a forked child crashes
   it.

**Port already in use**
   Another process holds the port. Find it and free it:

   .. code-block:: console

      $ lsof -nP -iTCP:8080 -sTCP:LISTEN
      $ lsof -tiTCP:8080 -sTCP:LISTEN | xargs kill

Pool behaviour
--------------

**The pool never grows beyond one worker**
   Expected on a small site. ``worker_max_users`` is unset by default, so one
   worker takes everybody; growth then depends on measured occupancy, and idle
   sessions do not move it. Set ``KAJENN_WORKER_MAX_USERS`` to force the spread —
   ``1`` gives every user a worker of his own.

**A request is answered 503**
   Nobody admitted the user and no worker could be born — the group's memory
   quota is full and nothing can leave. It is a refusal, not a fault.

**A user's session seems to reset between requests**
   Routing depends on the ``spa_connection_id`` cookie, which carries the
   connection id the site minted while serving. A client that drops cookies is a
   new visitor at every request and is placed as one. Make sure the client keeps
   cookies across requests.

**A shared global value looks stale on another worker**
   There is no replica to lag. The master is one dictionary on the commander: a
   worker reads it with a call and writes through a grant that lands all at once.
   A value that looks stale is a value nobody has written yet. See the sharing
   section of :doc:`the-pool`.

**A page stops receiving changes after the user was idle**
   What waits at the desk for a user going into the freezer is lost with the
   websockets that would have carried it: the queues are ephemeral and are not
   frozen with him. His state comes back; what was in flight does not.

Observation
-----------

**``/_server/...`` answers 404**
   The built-in recipe declares no ``_server`` application, and a server that
   declares none exposes none. Use ``/metrics``, or write a ``--config`` recipe
   that declares the ``_server`` application together with an administrator and a
   storage key.

**``/metrics`` shows fewer event lines than expected**
   ``genropy_site_events`` is a counter family: a counter appears only once it
   has been incremented. The three ``genropy_site_counters`` population lines are
   always there.

A stale build being served
--------------------------

If behaviour does not match the code you expect, confirm no old server is still
listening — a pool left running from an earlier launch keeps serving its old
code:

.. code-block:: console

   $ lsof -nP -iTCP:8080 -sTCP:LISTEN     # is anything still there?
   $ lsof -tiTCP:8080 -sTCP:LISTEN | xargs kill

Then relaunch. ``--reload`` does not help: it is accepted and ignored, because
the core server has no reloader.
