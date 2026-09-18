The pool
========

A genropy site is synchronous Python: one process serves through one thread pool
and saturates at a few concurrent users. genropy-kajenn runs the site in several
processes and pins each user to one of them.

There is nothing to choose and nothing to size. The pool always runs, and this
page says what it does on its own. The machinery itself is kajenn-orchestra's —
the group handler, the placement, the freezer — and its documentation describes
it in full at https://kajenn-orchestra.readthedocs.io/en/latest/ . What follows
is that behaviour as a genropy site meets it, plus what this package sets.

Where a user lives
------------------

**All the pages of one user live in the same process as his state.** That is the
founding rule and everything else follows from it. A grid filtered over six
hundred thousand rows, a document being composed, a tree of selections: that
context lives in the memory of the process serving him, so every request of his
must reach that process.

Routing is by identity, not by connection. The ``spa_connection_id`` cookie
carries the connection id **the site itself minted while serving** — the front
mints nothing and keeps no state of its own. The commander knows whose that id
is, which group he belongs to and which worker holds him.

A client that drops cookies is a new visitor at every request. That is the one
thing that breaks the pinning, and it breaks it the same way it breaks a session
under ``gnrwsgiserve``.

How the pool grows
------------------

It starts with **one** worker — the reception, which is a role and not a count,
and which is simply the oldest living worker. After that:

* a newcomer is offered to the workers already running, **fullest first**, so
  what is already warm is filled before anything new is started;
* a worker judges itself on its own last measurement and refuses by raising:
  over its setpoint, or already holding as many users as it may;
* when nobody admits him, one more worker is born if the group's memory quota
  affords it, and the newcomer waits for that birth rather than being turned
  away;
* when nobody admits him and nobody can be born, the request is answered
  ``503``.

When the load falls the pool shrinks: the coldest worker is closed, and only if
what it holds fits on the survivors. A worker younger than the group's minimum
life is never the one closed.

The number of processes is a reading, never a setting. The group's memory quota
is sized for ``worker_max_number`` workers, which defaults to 6 in
kajenn-orchestra and which the built-in recipe does not change.

Workers are born by fork
------------------------

A ``GnrWsgiSite`` is expensive to build. The group therefore owns a **template
process** that builds it once, and every worker of the group is a ``fork`` of
that template. Starting one more worker costs a fork, not a cold start.

``GenropySiteEngineFactory`` is what the template runs. It settles the two lazy
resolutions a first request would otherwise force in every worker
(``resources_dirs`` and ``storage("gnr")``) and closes the database connection
before the fork, so no child inherits an open socket.

This is why ``PGGSSENCMODE=disable`` is needed on macOS: libpq negotiating
Kerberos inside a forked child crashes it.

When a user goes quiet
----------------------

A user who stops asking anything is **frozen**: his state is written to the
freezer and his worker gets the memory back. His next request wakes him wherever
there is room — not necessarily on the worker he left.

How long the silence must last is ``KAJENN_IDLE_FREEZE_MINUTES``. Unset, the
worker reads the site's own ``<cleanup>`` section — ``connection_max_age``, in
seconds — and 7200 seconds where the site says nothing.

The freezer lives inside the site's ``data`` directory by default, because a
frozen user is kept for days and that directory is the one that survives.
``KAJENN_FROZEN_USERS_PATH`` moves it.

The legacy ``<cleanup>`` ages have no other equivalent here.
``connection_max_age`` was the silence past which the legacy register dropped a
logged connection; on this base the same silence parks the user in the freezer
instead. ``page_max_age`` and ``guest_max_age`` map to nothing: a silent tab's
row lives until the site drops it or its user freezes.

Restarting does not log anybody out
-----------------------------------

On the way down every worker parks its users frozen and the commander writes its
own maps beside them. On the way up the maps come back and nobody is pre-warmed:
the first request of a person is what wakes him. The browser comes back with the
same cookie, the same identity, and no new login.

What is shared, and what is not
-------------------------------

* **Per user** — his pages, their live data, his own store. All in his worker,
  and immediately coherent there.
* **Global** — the legacy ``globalStore()`` is one dictionary on the commander,
  behind one FIFO lock, with **no replica anywhere**. A worker reads it with a
  call and writes it through a grant that lands all at once. A value that looks
  stale is a value nobody has written yet.
* **Between users** — a change one page makes, or a table event, is delivered
  **addressed**: only to the pages that subscribed it, wherever they sit. See
  :doc:`architecture/overview`.

Watch it
--------

``/metrics`` gives the site-wide counters with no authentication, served by the
front in the server process. It is the only observation surface the built-in
recipe exposes.

kajenn's ``_server`` application — with its monitor section under
``/_server/monitor/`` — is **not** part of that recipe. A server that declares no
``_server`` application exposes no ``/_server/...`` at all. To have it, write a
``--config`` recipe that declares it; its routes are gated ``SERVER_ADMIN``, so
the same recipe must also declare an administrator and the storage key the user
store encrypts with.

For the questions nobody predicted there is the console: set ``KAJENN_CONSOLE``
and the pool's debug door is mounted on ``/_console`` as MCP tools, evaluating an
expression inside the commander or inside a named worker. It reads the live
registers without going through the site, so looking leaves no trace in what it
observes.

.. warning::

   The console is full ``eval`` by construction — there is no read-only ``eval``
   in Python. Mounting **is** the gate: unset, the door does not exist. Never set
   it in production.
