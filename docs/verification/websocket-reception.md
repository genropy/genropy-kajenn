# WebSocket milestones: reception and ephemeral-page RPC

Recorded on the predecessor, genropy/genropy-asgi, in September 2026, and carried
here with the code. Every count and every browser observation below belongs to
that run; this repository's suite has not repeated the live parts.

The reception milestone is complete. The next increment now executes ordinary
page RPC through the same ephemeral-page lifecycle as HTTP. HTTP continues unchanged.

## The reception probe, removed on 2026-09-24

The reception milestone (step 3 below) was verified through a diagnostic route,
`/_websocket_receive`. `WebSocketReceiver` answered a WSK call on that path
itself, without reaching the site: it checked for a page ID, a method name and a
parameters object, and replied `received: true`, `executed: false`, with the page
ID, the method and the worker PID. The page `tests/fixtures/wsx_probe.py` called
it from the browser; its only rpc raised if the call ever reached the dispatcher.

The route was removed before the bridge's first WSK merge (genropy/genropy-kajenn#1),
together with `wsx_probe.py` and the tests that called it. Reasons: no client calls
it once page RPC runs (step 4); it answered any page holding an open channel; it
logged every call at INFO. Every WSK call now goes to the page's ordinary RPC path.
The records below mention the route and the probe page as they were during the
2026-09-09 session; they describe that session, not the current code.

## Plan and status

1. Select the bridge's Python handler instead of opening `async.sock`: implemented
   and import-tested.
2. Select the WSX JavaScript client during legacy bootstrap: implemented and
   verified in a real browser with a legacy page.
3. Open the page channel, route a call through the core to the owning worker,
   log receipt and acknowledge without execution: verified end to end.
4. Adapt a page RPC to the normal legacy lifecycle, preserve its response and
   compare HTTP/WSK success, handled errors and fresh instances: verified with
   the real site and browser.

Resident pages and alternatives to mixins remain separate framework research.

## Ephemeral-page RPC increment

`genro.wsk.call` now serializes parameters through the legacy serializer and sends
the URL-encoded form inside WSX to the page's ordinary RPC path. The worker verifies
the form agrees with the channel page ID, translates it to a POST environ, preserves
the trusted identity and delegates to the existing WSGI application. The site creates
the page and performs its normal dispatch and cleanup. The adapter does not call
getWsMethod or retain a page instance.

The adapter carries the original response body as text inside a TYTX envelope,
with content-type and profiling headers. It does not expose Set-Cookie to JavaScript.
For Bag replies, the browser uses the existing RPC resultHandler on the original
XML: existing result decoding, resource loading and datachanges handling are reused.
JSON result mode is also accepted. Other modes are explicitly refused for now.

The fixture `tests/fixtures/wsx_rpc.py`, installed beside wsx_probe (since removed), provides
`/webpages/wsx_rpc` with HTTP/WSK buttons. Its result contains an integer, date,
decimal and a fresh invocation ID. A handled error followed by another call verifies
recovery; constructor and method probes verify currentPage is clear before construction
and points at the executing instance during dispatch. This is evidence for the tested
lifecycle, not a complete audit of every database/transaction cleanup path.

```sh
GNR_WSX_TEST_URL=http://127.0.0.1:18971 python tests/test_websocket_rpc.py
```

The original reception button now calls the probe route explicitly rather than
using the application RPC entry point.

Final verification of this increment: all 12 tests in `test_websocket*.py` passed
with both live tests enabled. In the browser, a handled WSK error returned
`gnrsilent`; the next WSK call succeeded, and its values matched the HTTP call.
Each call reported a different invocation ID. Flake8 on the added Python code,
JavaScript syntax checking and git whitespace checks passed.

## Integration

The companion genropy compatibility worktree provides the
`GNR_DAEMON_PROVIDER` switch. The bridge CLI selects `genropy-kajenn`; its
`gnr.web:websockethandler` entry point exports the handler. Without the environment
selection, classic genropy retains its original handler.

The provider returns True from `checkSocket` and ignores `sendCommandToPage`,
including the old `registerNewPage` command. Its `client_module` selects
`gnrwebsocket_kajenn.js`. Site WebSocket enablement is still required.

The client uses the current origin and opens `/_wsx/openchannel` with the page ID.
It now sends application calls to the page's ordinary RPC path. The core validates
channel ownership and transports WSK to the worker. `WebSocketReceiver` wraps the
worker's WSGI application and adapts these calls as described above. Logs do not
contain application parameter values.

## Verification performed on 2026-09-09

The live test used `test_invoice_pg` on localhost port 18971 with the companion
genropy worktree on PYTHONPATH. A temporary engine factory enabled WebSockets in
memory, pointed `site.gnr_path['11']` to the compatibility worktree's
`gnrjs/gnr_d11`, and pointed `site.site_static_dir` to a temporary static folder.
At this initial reception-only stage, no persistent site configuration was changed. The fixture
`tests/fixtures/wsx_probe.py` was placed in that folder's `webpages` directory.

Opening `/webpages/wsx_probe` in the browser and pressing **Send websocket call**
returned `received: true, executed: false` from worker PID 63178. The worker log
recorded the same page and method. The fixture's method raises if invoked;
the WSK path did not invoke it.

Eight Python tests passed (three provider tests, four receiver tests and one
live test). The live test verifies foreign-page refusal (403), channel opening,
two separately correlated acknowledgements and invalid-call refusal (400).
The new JavaScript also passed Node's syntax check.

With the test site running and both worktrees available to the interpreter:

```sh
python tests/test_websocket_provider.py
GNR_WSX_TEST_URL=http://127.0.0.1:18971 python tests/test_websocket_reception.py
```

Without `GNR_WSX_TEST_URL`, the live test is skipped; the receiver tests still run.
The provider tests require the companion legacy source on PYTHONPATH and exercise
real entry-point discovery in fresh interpreters.

## Deliberate limits

This is initial page-RPC support, not complete WebSocket application support:
no automatic reconnection/replay, addressed push, shared objects or event forwarding.
The outer JS codec handles JSON; legacy parameter encoding and XML results carry
genropy types. Bag results with integer/date/decimal values were compared against
HTTP, but every possible legacy type has not been exercised. File streaming,
cookie-changing authentication flows and full parity of all HTTP call options are
outside this increment. Calls time out and pending calls fail on disconnect. Old
outbound commands are intentionally ignored, and the provider does not yet implement
the whole legacy outbound helper API. Server-side push/datachanges behavior still
needs its own adoption work even though client envelope processing is reused.

Integration validation: the full bridge suite passed with 282 tests and two
optional benchmark tests skipped. Ruff passed across the repository.


## Current iteration closed — 2026-09-09

The current exploration is considered complete by scope agreement. The project
owner reports that WebSockets were practically unused in legacy production;
full parity with gnrasync is therefore not a requirement for this iteration.
The acceptance criterion is demonstrated delivery and execution of legacy WSK
calls through kajenn, with the result returned to the browser.

Evidence includes the original legacy websocket test page, copied unchanged to
the temporary test site: both its WSK and HTTP buttons returned `test ok`.
The test15 dbSelect comparison also returned the same search results through
HTTP and WSK, and a WSK result was selected successfully. The worker log confirms
`app.dbSelect` used WSK. For that second page only, the unrelated TableHandler on
`fatt.fattura` was removed from a temporary copy because the test instance lacks
that package. The repository's original test pages were not modified.

The page-class cache was subsequently enabled in test_invoice_pg instanceconfig
and remains enabled by agreement. A live diagnostic confirmed class reuse, and
all 12 targeted websocket tests passed, including live reception and RPC tests.
The browser latency runs and their limitations are recorded in
`websocket-latency.md`.

Unsolicited server-to-browser updates are a nice-to-have investigation tracked
in genropy/genropy-asgi#20, not a closure requirement.
Shared objects are separate work. Resident-page design is outside this iteration
and refers to the project's own model; these demonstrated calls still use fresh
request instances. The deliberate limits above remain applicable.

This closes the exploratory iteration, not a release or a claim of full legacy
WebSocket compatibility. The bridge and companion legacy changes are maintained in separate compatibility
branches. Integration and release are tracked separately from this scope closure.


## Live run after the probe removal — 2026-09-24

Run on this repository, not on the predecessor. Bridge at `cbd5e64` (the head of
genropy/genropy-kajenn#1 before its squash merge), genropy `origin/develop` at
`54bfe1d1da`, which carries genropy/genropy#1396 (the websocket-provider selector)
and genropy/genropy#1400 (the client closes a refused channel). PostgreSQL local.

Result: `tests/test_websocket_reception.py`, `tests/test_websocket_rpc.py` and
`tests/test_websocket_provider.py` → 12 passed, the two live tests included.

Setup, as it was needed on that machine:

- genropy `develop` in a detached worktree; its `gnrpy` goes on `PYTHONPATH`
  ahead of the genropy installed in `.venv`.
- `GNR_LOCAL_PROJECTS=<worktree>/projects`: `PathResolver` looks there before the
  projects of `~/.gnr/environment.xml`. On `develop` the site is
  `projects/test_invoice/instances/test_invoice_pg`, found through its `root.py`;
  `GnrWsgiSite` resolves the site by name only, so passing a path to `gnrkajenn`
  does not reach the worker.
- `psycopg2-binary` in `.venv`: the site's database adapter. It is not a declared
  dependency.
- `tests/fixtures/wsx_rpc.py` copied to `<site>/webpages/wsx_rpc.py`: `/webpages/`
  resolves to the site's `site_static_dir`, which for this site is the instance's
  `site` folder.
- No site configuration change: with `GNR_DAEMON_PROVIDER=genropy-kajenn` genropy
  `develop` turns the site's WebSockets on by itself (#1396).

```sh
W=<genropy develop worktree>
GNR_LOCAL_PROJECTS=$W/projects PYTHONPATH=$W/gnrpy GNR_DAEMON_PROVIDER=genropy-kajenn \
PGGSSENCMODE=disable .venv/bin/gnrkajenn test_invoice_pg -p 18971 --nodebug

GNR_WSX_TEST_URL=http://127.0.0.1:18971 PYTHONPATH=$W/gnrpy \
.venv/bin/python -m pytest tests/test_websocket_reception.py \
    tests/test_websocket_rpc.py tests/test_websocket_provider.py
```
