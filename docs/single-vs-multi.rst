Single or multi worker?
=======================

There is nothing to choose. **The pool always runs.** This page exists because
the question is asked, and because earlier versions of this package really did
have a selector.

There is no selector
--------------------

``gnrkajenn`` has no ``--workers`` option and no single/pool flag, and the
built-in recipe declares no worker count. What it declares is one group, named
``pool``; the group brings one worker into being at boot and every further worker
is born because a user arrived whom nobody admitted.

A ``KAJENN_WORKERS`` still set in the environment is reported by the command on
startup and ignored.

What a small site looks like
----------------------------

Left alone, ``worker_max_users`` is kajenn-orchestra's own default — unlimited —
so one worker takes everybody. A site with a handful of users therefore runs in
**one** worker process and behaves like a single process, without anyone
configuring that.

It is still a pool. The front and the commander are in the server process, the
site is in a worker process, and the request crosses a unix socket. What changes
under load is only how many worker processes there are.

How to make it spread
---------------------

Set ``KAJENN_WORKER_MAX_USERS``. It is how many users one worker may hold before
it refuses the next, and ``1`` puts every user on a worker of his own — which is
what a test bench wants, because it is the only way the cross-worker paths get
exercised at all. A production site does not need it.

Everything else — when a worker is born, when one is closed, how full is too full
— is measured, not declared. See :doc:`the-pool`.
