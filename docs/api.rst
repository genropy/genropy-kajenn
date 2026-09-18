API reference
=============

genropy-kajenn is normally driven through the ``gnrkajenn`` command, not
imported. These pages document the modules for the cases where you embed the
bridge in a server of your own or extend it.

The root package exports only ``__version__``; everything useful lives in the
three subpackages below.

.. note::

   Autodoc mocks ``gnr`` and nothing else. genropy is a runtime requirement and
   is not installed where this documentation is built, while ``kajenn`` and
   ``kajenn_orchestra`` are real dependencies and are imported for real — so the
   base classes shown here are the real ones.

The SPA bridge
--------------

The front, the commander and the worker: the three processes' worth of classes
that host a genropy ``GnrWsgiSite``.

.. automodule:: genropy_kajenn.spa
   :no-index:

The front
~~~~~~~~~

.. automodule:: genropy_kajenn.spa.genropy_spa_application

The commander and its desk
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: genropy_kajenn.spa.genropy_spa_commander

.. automodule:: genropy_kajenn.spa.delivery_desk

.. automodule:: genropy_kajenn.spa.subscription_index

The worker
~~~~~~~~~~

.. automodule:: genropy_kajenn.spa.genropy_worker

.. automodule:: genropy_kajenn.spa.genropy_register

.. automodule:: genropy_kajenn.spa.legacy_bag

The site and the launch
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: genropy_kajenn.spa.site_engine_factory

.. automodule:: genropy_kajenn.spa.config

.. automodule:: genropy_kajenn.spa.cli

The OpenAPI bridge
------------------

A genropy database behind an ``OpenApiApplication`` — REST, and MCP through
``McpOpenApiApplication`` — with thread-local database cleanup.

.. automodule:: genropy_kajenn.proxy.genropy_proxy

The daemonless register
-----------------------

The in-process register the legacy imports as ``gnr.web.daemon``. You do not
instantiate it: the ``GnrWsgiSite`` builds it at ``site.register``.
``genropy_kajenn.siteregister.SiteRegisterClient`` is an alias of
``GenropyRegisterClient`` — the name the legacy imports.

.. automodule:: genropy_kajenn.siteregister

.. automodule:: genropy_kajenn.siteregister.global_store_adapter

.. automodule:: genropy_kajenn.siteregister.exceptions

.. automodule:: genropy_kajenn.siteregister.siteregister
