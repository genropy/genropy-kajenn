# Building the documentation

From the repository root, use an isolated environment and build with warnings as
errors:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[docs]'
sphinx-build -W --keep-going -b html docs docs/_build/html
python -m http.server 8769 --bind 127.0.0.1 --directory docs/_build/html
```

Open `http://127.0.0.1:8769/`. Stop that HTTP server with Ctrl-C. If the port is
occupied, choose another one; do not terminate someone else's server.

`conf.py` resolves `src` relative to itself, so invoking Sphinx from the
repository root or from `docs/` documents the same checkout.

## What autodoc needs, and what it mocks

Autodoc mocks `gnr` and nothing else.

- **genropy is absent on purpose.** It is a runtime requirement of the package
  and not a declared dependency, so it is not installed where the documentation
  builds. The modules that import `gnr.*` at their top —
  `spa/genropy_register.py`, `spa/legacy_bag.py`,
  `siteregister/siteregister_client.py`, `siteregister/global_store_adapter.py` —
  are documented against that mock.
- **kajenn and kajenn-orchestra are real.** They are declared dependencies, they
  install with the package, and autodoc imports them for real. Mocking `kajenn`
  while `kajenn_orchestra` is really installed puts a mock in the base chain of
  every class documented here, and autodoc's walk over that chain does not
  terminate. That is what made the Read the Docs build of commit `e9d9cf7` run
  until the 15-minute limit killed it.

Install genropy in the same environment if you want the `gnr.*`-importing modules
documented from the real classes:

```bash
python -m pip install genropy
```

## The diagrams

The architecture diagrams are Mermaid, written as ```` ```mermaid ```` fences in
the Markdown sources. `sphinxcontrib-mermaid` (in the `docs` extra) turns each
fence into a `<div class="mermaid">`, and `myst_fence_as_directive` is what lets
a Markdown fence reach that directive. The drawing happens **in the browser**,
from a CDN: `sphinx-build` never reports a diagram that fails to parse, so open
the built page and check that every fence became an `<svg>` before publishing.

## What is not built

Two directories under `docs/` are excluded by `exclude_patterns` and are not part
of this documentation:

- `docs/internal/` — working notes, every one of them headed
  `🔴 DA REVISIONARE`. Two are written in Italian
  (`performance_analysis.md` and `step1_spawner_design.md`); the rest are in
  English. They are not translated and not published.
- `docs/verification/` — the logs of live acceptance sessions, written as records
  of one run and not as procedures.

## Read the Docs

The repository's `.readthedocs.yaml` declares Ubuntu 24.04, Python 3.12,
installation of the `docs` extra, `docs/conf.py`, and failure on warnings.

The [genropy-kajenn Read the Docs project](https://app.readthedocs.org/projects/genropy-kajenn/)
exists and is connected to this repository; its default version is `latest`,
built from `main`, and its configured documentation URL is
<https://genropy-kajenn.readthedocs.io/en/latest/>.

:::{admonition} Under review
:class: warning

**No build has ever succeeded.** The two builds of commit `e9d9cf7` — `latest`
and `stable`, both on 2026-09-18 — were terminated at the 15-minute limit, and
the documentation URL answers 404 until one of them passes. The cause was the
`kajenn` mock described above, and it is fixed in this checkout; whether the
remote build then passes has to be read on the project page, not inferred here.
:::

Check the remote build result before claiming an update is live. Build
configuration is not evidence that a build was published.
