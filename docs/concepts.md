# Concepts

This page explains the model: what the legacy genropy stack does, what
genropy-kajenn does instead, and the words the rest of the documentation uses.
The classes are named with their module, all under `genropy_kajenn` unless the
text says otherwise.

## The problem

A legacy genropy site is synchronous Python behind the WSGI protocol. The legacy
stack serves it with two processes.

**`gnrwsgiserve`** runs the site under werkzeug, in one process. The work is
CPU-bound under the GIL, so that process saturates while the machine still has
cores to spare, and spreading the load across several of them meant an external
balancer plus session state shared by hand.

**`gnrdaemon`** is the site register, a process of its own reached over a wire —
Pyro4 first, then the `genro-nodaemon` TCP daemon. Every request touches it: who
is connected, which pages exist, who is logged in, which changes are waiting for
which page. It is one more process to launch, to keep alive and to debug when it
stops answering.

## The model

genropy-kajenn keeps the site exactly as it is and changes what stands around it.

**A commander in the server process.** The server process holds the front — the
mounted application that terminates HTTP — and, behind it, the commander that
knows who exists and where. `GenropySpaApplication`
(`spa/genropy_spa_application.py`) is that front; `GenropySpaCommander`
(`spa/genropy_spa_commander.py`) is that commander. Both are subclasses of
kajenn-orchestra's `SpaApplication` and `SpaCommander`: the generic machinery is
orchestra's, and this package adds the genropy fit.

**A supervised pool of worker processes.** Every worker is a separate process
running one `GenropyWorker` (`spa/genropy_worker.py`), which hosts one
`GnrWsgiSite` and assigns it to the seam the core serves HTTP through
(`self.wsgi_app`). The worker talks to its commander over a Unix socket. There is
no worker count to declare: the group starts with one worker and grows when the
workers it has admit nobody.

**Every user is pinned to one worker.** All the pages of one user live in the
same process as his state — a filtered grid, a document being composed, a tree of
selections. Routing is by identity: the `spa_connection_id` cookie carries the
connection id **the site itself minted while serving**, and the commander knows
whose it is and which worker holds him. The front mints nothing.

**No register daemon.** `GenropyRegisterClient`
(`siteregister/siteregister_client.py`) *is* the object the site builds at
`site.register`. It reaches its worker as `site.spa_worker` and calls the
worker's methods directly, in the same process, on the thread that is serving the
request. Every command the legacy calls is an explicit public method of that
class.

## How genropy finds the daemonless register

The legacy site imports its register from `gnr.web.daemon`. genropy resolves that
namespace through an entry-point gate, and the gate is closed unless it is asked
by name.

- `pyproject.toml` declares the entry point `gnr.web:daemon` pointing at
  `genropy_kajenn.siteregister`.
- genropy replaces its own `gnr.web.daemon` with that module **only when the
  environment variable `GNR_DAEMON_PROVIDER` names the provider**.
- `spa/cli.py` sets it: `DAEMON_PROVIDER = "genropy-kajenn"`, written with
  `os.environ.setdefault` before anything imports the site machinery.

The choice is therefore per process, not per installation: the classic
daemon-based stack and this one can share one virtualenv, because only the
process that declared the provider gets the in-process register.

`siteregister/` also carries `handler.py`, `service.py`, `processes.py` and
`siteregister.py`. They exist so that the `gnr.web.daemon.*` names the legacy
imports resolve; nothing in the request path calls them, and using them raises.

## The words

**Front.** The mounted application that terminates HTTP. It is mounted at the
**root** (`mount = ""`): a genropy site builds absolute URLs — `/_rsrc`, `/sys`,
the dojo tree — so a prefix would serve the first page and 404 everything that
page asks for. `GenropySpaApplication` refuses a non-empty `mount` at
construction.

**Commander.** The vertex in the server process: the populations, the placements,
the one global store, the freezer, and — the bridge's addition — the delivery
desk.

**Group.** One set of workers under one policy. The built-in recipe declares
exactly one, named `pool`.

**Template process.** A `GnrWsgiSite` is expensive to build, so the group builds
it **once**, in a template process, and forks its workers from there.
`GenropySiteEngineFactory` (`spa/site_engine_factory.py`) is what builds it: it
settles `resources_dirs` and `storage("gnr")` before the fork, and closes the
database connection so no child inherits an open socket.

**Freezer.** A user who stops asking anything has his state written to disk and
his worker gets the memory back. His next request wakes him wherever there is
room, not necessarily on the worker he left.

**Delivery desk.** The commander's index of who subscribes what and what waits
for whom: `DeliveryDesk` (`spa/delivery_desk.py`), attached to the commander's
dispatcher as the `delivery` branch. Its four routes are the calls a worker
places on `/commander/delivery/{subscribe_table,exchange,deposit,on_datachange}`.

## What travels between workers

Three things cross a process boundary, and nothing else does.

**Addressed writes (datachanges).** What one page writes for another page. A
write to a page of the caller's own user, living in the same worker, lands on
that page's row at once; every other address climbs to the desk as one call on
`/commander/delivery/on_datachange`, and waits in that page's queue until the
page collects.

**Table events (dbevents).** A page subscribes to a table with `subscribeTable`;
the subscription is filed at the desk synchronously. The desk keeps the whole set
of subscribed tables and pushes it down to every worker on every transition — a
table gaining its first subscriber, or losing its last — as the order
`/commander/delivery/subscribed_tables`. A worker's `notifyDbEvents` filters the
commit's events against that set at the source: a table nobody subscribes is not
announced at all. What survives the filter is laid on the request's own slot
(`GenropyRequestSlot`) and leaves at the end of the request.

**The global store.** The legacy `globalStore()` is **one dictionary on the
commander**, behind one FIFO lock, with no replica anywhere. A worker reads it
with a call and writes it through a grant. `GlobalStoreAdapter`
(`siteregister/global_store_adapter.py`) is the only place where the legacy
dotted path meets that dictionary: the first path segment is the dictionary key,
the rest of the path lives inside the legacy `Bag` stored under it. A subpath
write holds a keyed read-modify-write turn, so a sibling leaf another worker
wrote is not dropped; a `with globalStore()` block holds the whole dictionary for
its thread and publishes it once, on the exit.

Per-user and per-page state crosses nothing: it lives in one worker and is
immediately coherent there.

## What stays legacy

The `Bag` that rides the registers is the legacy `gnr.core.gnrbag.Bag`, not the
new `genro_bag.Bag`, and the two are never converted into each other.
`LegacyBagCollector` (`spa/legacy_bag.py`) is the capture attached to it, and
importing that module registers the legacy Bag with genro-tytx under the wire
code `BAG`. Authentication, sessions and page rendering stay inside the
`GnrWsgiSite`, not in the ASGI layer.
