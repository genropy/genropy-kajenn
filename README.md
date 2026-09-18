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
own process, so the classic stack and this one can share one virtualenv.

Your site does not change: same `root.py`, same packages, same authentication,
same pages.

## Installation

```bash
pip install genropy-kajenn
```

`kajenn` and `kajenn-orchestra` are installed with it. **genropy must be present
at runtime** and configured as usual (`~/.gnr/environment.xml` plus an existing
site); it is deliberately not a declared dependency of this package.

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

## License

Apache License 2.0 — Copyright 2025 Softwell S.r.l. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
