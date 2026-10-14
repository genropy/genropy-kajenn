# genropy-kajenn

[![PyPI](https://img.shields.io/pypi/v/genropy-kajenn)](https://pypi.org/project/genropy-kajenn/)
[![Tests](https://github.com/genropy/genropy-kajenn/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/genropy/genropy-kajenn/actions/workflows/tests.yml)
[![Codecov](https://codecov.io/gh/genropy/genropy-kajenn/branch/main/graph/badge.svg)](https://app.codecov.io/gh/genropy/genropy-kajenn)
[![Documentation](https://readthedocs.org/projects/genropy-kajenn/badge/?version=latest)](https://genropy-kajenn.readthedocs.io/en/latest/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://github.com/genropy/genropy-kajenn/blob/main/pyproject.toml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

*genropy legacy sites on kajenn: a commander in the server, a supervised pool of
workers each hosting one site, users pinned to a worker, no register daemon.*

genropy-kajenn serves an existing, synchronous **genropy** site on an ASGI
server. It replaces two pieces of the legacy stack at once: `gnrwsgiserve`, the
one-process werkzeug launcher, and `gnrdaemon`, the register daemon reached over
a wire.

One server process holds the front and the commander. Every worker is a process
of its own hosting one unmodified `GnrWsgiSite`, born by `fork` out of a template
process that builds that site once for the whole group. A user and all his pages
live in one worker, and the `spa_connection_id` cookie — the connection id the
site itself minted — is what sends every request of his back to it. A user who
goes quiet is written to a freezer on disk and his worker gets the memory back;
his next request wakes him wherever there is room.

The site register is answered **in-process**. The package declares the
`gnr.web:daemon` entry point, and genropy installs it as `gnr.web.daemon` only
when `GNR_DAEMON_PROVIDER` names the provider — which the command does for its
own process, so the classic stack and this one can share one virtualenv. That gate
exists only in genropy `develop` (see Installation).

Your site does not change: same `root.py`, same packages, same authentication,
same pages.

## Installation

```bash
pip install genropy-kajenn
```

`kajenn` and `kajenn-orchestra` are installed with it. **genropy must be present
at runtime** and configured as usual (`~/.gnr/environment.xml` plus an existing
site); it is deliberately not a declared dependency of this package.

**genropy must come from its `develop` branch.** genropy-kajenn needs genropy
commits `9810aa4f1a` (the `GNR_DAEMON_PROVIDER` gate), `436c805006`
(`websocketHandlerClass`, `gnrwebsocket_kajenn.js`) and `add8e38b8d` (the browser
socket closed when its channel is refused). The latest PyPI release, genropy
26.9.29 (tag `release-26.09.29`), contains none of them. Details:
[genropy prerequisite](https://genropy-kajenn.readthedocs.io/en/latest/getting-started.html#genropy-develop).

## Usage

```bash
gnrkajenn mysite -p 8080
```

`mysite` is the genropy instance name — the same you pass to `gnrwsgiserve` — or
a path to a site directory. That is the whole launch: no worker count to declare
and no single/pool selector. On macOS export `PGGSSENCMODE=disable`, because
libpq negotiating Kerberos inside a forked child crashes it.

Site-wide counters, no authentication needed:

```bash
curl -s http://127.0.0.1:8080/metrics
```

## Documentation

<https://genropy-kajenn.readthedocs.io/en/latest/> — concepts, architecture with
diagrams, the CLI, the configuration keys, the FAQ and troubleshooting. To build
it locally see [`docs/building.md`](docs/building.md):

```bash
pip install -e ".[docs]"
sphinx-build -W --keep-going -b html docs docs/_build/html
```

Underneath: [kajenn](https://kajenn.readthedocs.io/en/latest/) is the ASGI
server, [kajenn-orchestra](https://kajenn-orchestra.readthedocs.io/en/latest/)
the commander/worker orchestration.

## Development

```bash
pip install -e ".[dev]"
pytest tests/
ruff check src/ tests/
```

The live tests host the `test_invoice_pg` instance of genropy and need:

- a genropy checkout (the `develop` branch), installed with
  `pip install -e "gnrpy[pgsql]"` plus the `requirements.txt` of the
  `gnrcore/adm` package;
- a genro configuration folder named by `GENRO_GNRFOLDER`, whose
  `environment.xml` points at that checkout (`gnrhome`, `projects`, `packages`,
  `resources`, `webtools`); the folder itself must be called `gnr`, because
  genropy reads its files under the folder's name (`gnr.environment_xml`),
  and kept outside any directory on `sys.path`, where it would shadow the `gnr`
  package;
- a running PostgreSQL, reached with the libpq variables (`PGUSER`,
  `PGPASSWORD`, `PGHOST`);
- in the configuration folder, `instanceconfig/default.xml` (an empty
  `<packages/>`) and `siteconfig/default.xml` (`<jslib dojo_version="11"
  gnr_version="11"/>` plus `<resources><common/><js_libs/></resources>`);
- in `environment.xml`, a `<static><js>` block with `dojo_11` at
  `dojo_libs/dojo_11` (`cdn=""`) and `gnr_11` at `gnrjs/gnr_d11` of the checkout;
- the database created with `createdb test_invoice_pg` and then built with
  `gnr app dbsetup test_invoice_pg`.

The suite skips only for genropy not installed, a database driver not installed,
an opt-in variable not set (`BENCH_*`, `GNR_BENCH_*`, `GNR_WSX_TEST_URL`) and an
installed genropy without `websocketHandlerClass`. Any other missing prerequisite
fails the run. `.github/workflows/tests.yml` builds all of the above.

## License

Apache License 2.0 — Copyright 2025 Softwell S.r.l. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
